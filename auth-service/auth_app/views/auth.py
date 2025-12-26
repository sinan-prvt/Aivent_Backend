from django.contrib.auth import get_user_model
from auth_app.utils import qrcode_base64_from_uri
from rest_framework import status, permissions, serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..serializers import (
    CustomLoginSerializer,
    RegisterSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from auth_app.core.captcha_utils import (
    requires_captcha,
    increment_failed_attempts,
    reset_failed_attempts,
)
from auth_app.core.recaptcha import verify_recaptcha
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from ..utils import create_otp_for_user
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.conf import settings
import logging
import pyotp
from auth_app.integrations.sqs_email import send_email_via_sqs
from auth_app.models import MFAChallenge
from django.utils import timezone
from datetime import timedelta
import secrets


User = get_user_model()

logger = logging.getLogger(__name__)


class MeView(APIView): 
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs): 
        user = request.user

        payload = { 
            "id": str(getattr(user, "id", "")), 
            "username": getattr(user, "username", "") or "", 
            "email": getattr(user, "email", "") or "", 
            "full_name": getattr(user, "full_name", "") or "", 
            "phone": getattr(user, "phone", "") or None, 
            "role": getattr(user, "role", "customer"), 
            "email_verified": bool(getattr(user, "email_verified", False)), 
            "vendor_approved": bool(getattr(user, "vendor_approved", False)), 
            "is_active": bool(getattr(user, "is_active", False)), 
            "date_joined": (getattr(user, "date_joined", None).isoformat() 
                if getattr(user, "date_joined", None) else None), 
            }
        return Response(payload, status=200)



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomLoginSerializer

    @swagger_auto_schema(
        operation_description="Login with email + password + reCAPTCHA + optional MFA",
        tags=["Authentication"]
    )

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        ip = request.META.get("REMOTE_ADDR")
        key = f"{email}:{ip}" if email else ip

        if requires_captcha(key):
            token = request.data.get("recaptcha_token")

            if not token:
                return Response({
                    "success": False,
                    "message": "reCAPTCHA required",
                    "errors": {"recaptcha": ["This action requires reCAPTCHA verification"]}
                }, status=status.HTTP_400_BAD_REQUEST)

            resp = verify_recaptcha(token, remoteip=ip)
            score = resp.get("score") or 0
            if not resp.get("success") or score < float(settings.RECAPTCHA_MIN_SCORE):
                increment_failed_attempts(key)
                return Response({
                    "success": False,
                    "message": "reCAPTCHA validation failed",
                    "errors": {"recaptcha": ["validation failed"], "score": [score]}
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            try:
                increment_failed_attempts(key)
            except Exception:
                pass
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        
        user = getattr(serializer, "_validated_user", None)
        reset_failed_attempts(key)

        if not user:
            return Response({"detail":"Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)
        

        if user.role == "vendor":

            if not user.vendor_approved:
                return Response(
                    {"detail": "Vendor approval pending"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # FIRST TIME MFA SETUP
            if not user.totp_secret:
                secret = pyotp.random_base32()
                user.totp_secret = secret
                user.totp_enabled = False
                user.save(update_fields=["totp_secret", "totp_enabled"])

                issuer = getattr(settings, "TOTP_ISSUER", "AIVENT")
                otpauth_url = pyotp.TOTP(secret).provisioning_uri(
                    name=user.email,
                    issuer_name=issuer
                )
                qr_code = qrcode_base64_from_uri(otpauth_url)

                return Response({
                    "mfa_required": True,
                    "mfa_setup": True,
                    "role": "vendor",
                    "otpauth_url": otpauth_url,
                    "qr_code": qr_code,
                }, status=200)

            # MFA VERIFY STEP
            challenge = MFAChallenge.objects.create(
                user=user,
                token=secrets.token_urlsafe(32),
                expires_at=timezone.now() + timedelta(minutes=5)
            )

            return Response({
                "mfa_required": True,
                "mfa_setup": False,
                "role": "vendor",
                "mfa_token": challenge.token,
                "expires_in": 300
            }, status=200)

        
        tokens_resp = super().post(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Logged in",
            "data": tokens_resp.data
        }, status=tokens_resp.status_code)
    



class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user with email + password + OTP verification",
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        raw_otp, otp_obj = create_otp_for_user(user, "email_verify")

        send_email_via_sqs(
            subject="AIVENT OTP Verification",
            to_email=user.email,
            template="otp",
            data={"otp": raw_otp},
        )

        return Response(
            {"detail": "User registered. OTP sent for email verification."},
            status=status.HTTP_201_CREATED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout by blacklisting refresh token",
        tags=["Authentication"]
    )

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "Could not blacklist token"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)


class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout from all devices by blacklisting all tokens",
        tags=["Authentication"]
    )

    def post(self, request, *args, **kwargs):
        tokens = OutstandingToken.objects.filter(user=request.user)

        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)
        return Response({"detail": "All tokens revoked"}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change user password",
        tags=["Authentication"]
    )

    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old = serializer.validated_data["old_password"]
        new = serializer.validated_data["new_password"]

        if not user.check_password(old):
            return Response(
                {"detail": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new)
        user.save()

        return Response({"detail": "Password changed successfully"}, status=200)
   