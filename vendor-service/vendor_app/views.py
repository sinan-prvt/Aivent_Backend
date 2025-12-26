import os
import requests
from django.conf import settings
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import VendorProfile
from .serializers import VendorApplySerializer, VendorProfileSerializer, VendorConfirmSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from vendor_app.permissions import IsAdmin 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from django.db import transaction


logger = logging.getLogger(__name__)


auth_base = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000/api/auth").rstrip("/")
auth_url = f"{auth_base}/internal/users/"


@method_decorator(csrf_exempt, name="dispatch")
class VendorApplyView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = VendorApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        existing = VendorProfile.objects.filter(
            email=email,
            status="pending"
        ).first()

        if existing:
            return Response(
                {
                    "detail": "Vendor application already pending",
                    "vendor_id": str(existing.id),
                },
                status=409,
            )

        vendor = serializer.save(status="pending")

        # create user in auth-service
        user_resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/internal/users/",
            json={"email": email, "role": "vendor"},
            headers={"X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN},
            timeout=5,
        )

        if user_resp.status_code not in (200, 201, 409):
            raise RuntimeError("Auth service user creation failed")

        # send OTP
        requests.post(
            f"{settings.AUTH_SERVICE_URL}/send-otp/",
            json={"email": email, "purpose": "email_verify"},
            timeout=5,
        )

        return Response(
            {
                "message": "OTP sent via auth-service",
                "vendor_id": str(vendor.id),
            },
            status=201,
        )


class VendorConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VendorConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vendor_id = serializer.validated_data["vendor_id"]
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        vendor = get_object_or_404(
            VendorProfile,
            id=vendor_id,
            email=email,
            status="pending"
        )

        otp_resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/verify-otp/",
            json={"email": email, "otp": otp, "purpose": "email_verify"},
            timeout=5,
        )

        if otp_resp.status_code != 200:
            return Response({"detail": "Invalid or expired OTP"}, status=400)

        if vendor.user_id:
            return Response({"detail": "Vendor already confirmed"}, status=409)

        user_resp = requests.get(
            f"{settings.AUTH_SERVICE_URL}/internal/users/by-email/",
            params={"email": email},
            headers={"X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN},
            timeout=5,
        )

        if user_resp.status_code != 200:
            return Response({"detail": "Auth user not found"}, status=500)

        vendor.user_id = user_resp.json()["id"]
        vendor.save(update_fields=["user_id"])

        return Response(
            {"detail": "Vendor confirmed. Await admin approval."},
            status=200,
        )


class PendingVendorsView(generics.ListAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return VendorProfile.objects.filter(status="pending")

class InternalVendorApproveView(APIView):
    def patch(self, request):
        if request.headers.get("X-Internal-Token") != settings.AUTH_SERVICE_INTERNAL_TOKEN:
            return Response({"detail": "Forbidden"}, status=403)

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id required"}, status=400)

        vendor = VendorProfile.objects.filter(
            user_id=user_id,
            status="pending"
        ).first()

        if not vendor:
            return Response({"detail": "Vendor profile not found"}, status=404)

        vendor.status = "approved"
        vendor.save(update_fields=["status"])

        return Response({"detail": "Vendor profile approved"}, status=200)