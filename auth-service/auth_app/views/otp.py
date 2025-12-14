from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from ..serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from ..utils import create_otp_for_user, verify_otp_entry
from auth_app.tasks import send_email_task
from django.conf import settings
from ..models import OTP
from django.utils import timezone


User = get_user_model()


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Send OTP for email verification or password reset",
        tags=["OTP"]
    )

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        raw_otp, otp_obj = create_otp_for_user(user, purpose)

        send_email_task.delay(
            subject="AIVENT OTP Verification",
            message=f"Your OTP is: {raw_otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"detail": "OTP sent"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify OTP for email verification or actions",
        tags=["OTP"]
    )

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp_value = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        otp_obj = OTP.objects.filter(
            user=user, 
            purpose=purpose, 
            used=False, 
            expires_at__gt=timezone.now()
        ).order_by("-created_at").first()

        if not otp_obj:
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_otp_entry(otp_obj, otp_value):
            return Response({"detail": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.used = True
        otp_obj.save()

        if purpose == "email_verify":
            user.email_verified = True
            user.is_active = True 
            user.save()

        if purpose == "reset_password":
            otp_obj.used = True
            otp_obj.save()

        return Response({"detail": "OTP verified successfully"}, status=status.HTTP_200_OK)


class SendResetOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Send OTP for resetting password",
        tags=["Password Reset"]
    )

    def post(self, request):
        serializers = SendOTPSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)

        email = serializers.validated_data["email"]
        
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        raw_otp, otp_obj = create_otp_for_user(user, "reset_password")

        send_email_task.delay(
            subject="AIVENT Password Reset OTP",
            message=f"Your OTP is: {raw_otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        
        return Response({"detail": "Reset OTP sent"}, status=status.HTTP_200_OK)

