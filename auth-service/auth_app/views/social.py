from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..social_auth import google_exchange_code, google_get_userinfo
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from auth_app.microsoft import microsoft_exchange_code


User = get_user_model()


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "Missing authorization code"}, status=status.HTTP_400_BAD_REQUEST)

        token_data = google_exchange_code(code)

        if "access_token" not in token_data:
            return Response({"detail": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

        access_token = token_data["access_token"]
        userinfo = google_get_userinfo(access_token)

        email = userinfo.get("email")
        name = userinfo.get("name", "User")

        if not email:
            return Response({"detail": "Google account has no email"}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": name,
                "email_verified": True,
                "role": "customer",
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
        })


class MicrosoftAuthView(APIView):
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "No code provided"}, status=status.HTTP_400_BAD_REQUEST)

        result = microsoft_exchange_code(code)

        if "error" in result:
            return Response({"detail": result.get("error_description")}, status=status.HTTP_400_BAD_REQUEST)

        claims = result.get("id_token_claims") or {}
        email = claims.get("email") or claims.get("preferred_username")
        name = claims.get("name", "")

        if not email:
            return Response({"detail": "Email not provided by Microsoft"}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": name,
            }
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name
            }
        })  
    
