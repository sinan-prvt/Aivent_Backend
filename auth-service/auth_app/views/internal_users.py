from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import status
import os
import secrets

User = get_user_model()
INTERNAL_TOKEN = os.getenv("AUTH_SERVICE_INTERNAL_TOKEN")

class InternalUserCreateView(APIView):
    def post(self, request):
        if request.headers.get("X-Internal-Token") != INTERNAL_TOKEN:
            return Response(
                {"detail": "Forbidden"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get("email")
        role = request.data.get("role", "customer")

        if not email:
            return Response(
                {"detail": "email required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "User already exists"}, 
                status=status.HTTP_409_CONFLICT
            )

        password = request.data.get("password")

        if not password:
            return Response(
                {"detail": "password required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


        username = email.split("@")[0]

        user = User.objects.create_user(
            email=email,
            password=password,
            username=username,
            role=role,
            is_active=False,
            email_verified=True,
            vendor_approved=False,
        )

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "temp_password": password,
            },
            status=status.HTTP_201_CREATED
        )


class InternalUserByEmail(APIView):
    def get(self, request):
        if request.headers.get("X-Internal-Token") != INTERNAL_TOKEN:
            return Response(
                {"detail": "Forbidden"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.query_params.get("email")
        if not email:
            return Response(
                {"detail": "email required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "id": str(user.id),
            "email": user.email,
            "role": user.role
        })