import pyotp
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class VerifyMFAView(APIView):
    permission_classes = [AllowAny]   # we authenticate by email+password earlier; we require email + password + code or the login step should have validated credentials

    def post(self, request):
        """
        Accepts: { "email": "...", "code": "123456" }
        On success -> returns access + refresh tokens
        """
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"detail":"email and code required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail":"User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.role != "vendor":
            return Response({"detail":"MFA only required for vendors"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.totp_secret:
            return Response({"detail":"TOTP not configured"}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            return Response({"detail":"Invalid TOTP code"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.totp_enabled:
            user.totp_enabled = True
            user.save(update_fields=["totp_enabled"])

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            "access": access,
            "refresh": refresh_token
        }, status=status.HTTP_200_OK)
