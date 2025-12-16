# auth_app/views/internal_users.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import status
import os
import secrets

User = get_user_model()
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")

class InternalUserCreateView(APIView):
    def post(self, request):
        if request.headers.get("X-Internal-Token") != INTERNAL_TOKEN:
            return Response({"detail": "Forbidden"}, status=403)

        email = request.data.get("email")
        role = request.data.get("role", "customer")

        if not email:
            return Response({"detail": "email required"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"detail": "User already exists"}, status=409)

        password = secrets.token_urlsafe(12)

        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            is_active=False,
            email_verified=True,
            vendor_approved=False,
        )

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "temp_password": password,
            },
            status=201
        )
