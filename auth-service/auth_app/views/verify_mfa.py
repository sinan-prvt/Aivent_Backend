import pyotp
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from auth_app.models import MFAChallenge
from django.utils import timezone

User = get_user_model()

class VerifyMFAView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("mfa_token")
        code = request.data.get("code")

        if not token or not code:
            return Response(
                {"detail": "mfa_token and code required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        challenge = MFAChallenge.objects.select_related("user").filter(
            token=token,
            expires_at__gt=timezone.now()
        ).first()

        if not challenge:
            return Response(
                {"detail": "Invalid or expired MFA challenge"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = challenge.user
        totp = pyotp.TOTP(user.totp_secret)

        if not totp.verify(code, valid_window=1):
            return Response(
                {"detail": "Invalid MFA code"},
                status=status.HTTP_400_BAD_REQUEST
            )

        challenge.delete()

        if not user.totp_enabled:
            user.totp_enabled = True
            user.save(update_fields=["totp_enabled"])

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["mfa"] = True

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
        })

