import os
import requests
from django.conf import settings
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import VendorProfile
from .serializers import VendorApplySerializer, VendorProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from vendor_app.permissions import IsAdmin 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging


logger = logging.getLogger(__name__)


auth_base = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000/api/auth").rstrip("/")
auth_url = f"{auth_base}/internal/users/"


@method_decorator(csrf_exempt, name="dispatch")
class VendorApplyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VendorApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data.get("email")

        # 🔒 BLOCK duplicate pending applications
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

        serializer = VendorApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save()


        # STEP 1 — CREATE USER IN AUTH-SERVICE
        user_resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/internal/users/",
            json={
                "email": email,
                "role": "vendor"
            },
            headers={
                "X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN
            },
            timeout=5
        )

        if user_resp.status_code not in (200, 201, 409):
            return Response(
                {"detail": "Failed to create auth user"},
                status=500
            )

        # STEP 2 — SEND OTP (VALID PURPOSE)
        requests.post(
            f"{settings.AUTH_SERVICE_URL}/send-otp/",
            json={
                "email": email,
                "purpose": "email_verify"
            },
            timeout=5
        )

        return Response(
            {
                "message": "OTP sent via auth-service",
                "vendor_id": str(vendor.id)
            },
            status=201
        )



class VendorConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        vendor_id = request.data.get("vendor_id")
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not vendor_id or not email or not otp:
            return Response(
                {"detail": "vendor_id, email, and otp are required"},
                status=400
            )

        vendor = get_object_or_404(VendorProfile, id=vendor_id)

        # STEP 1 — VERIFY OTP
        otp_resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/verify-otp/",
            json={
                "email": email,
                "otp": otp,
                "purpose": "email_verify"
            },
            timeout=5
        )

        if otp_resp.status_code != 200:
            return Response(
                {"detail": "Invalid or expired OTP"},
                status=400
            )

        # STEP 2 — FETCH USER BY EMAIL (INTERNAL)
        user_resp = requests.get(
            f"{settings.AUTH_SERVICE_URL}/internal/users/by-email/",
            params={"email": email},
            headers={
                "X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN
            },
            timeout=5
        )

        if user_resp.status_code != 200:
            return Response(
                {"detail": "Auth user not found"},
                status=500

            )

        # STEP 3 — LINK VENDOR PROFILE
        vendor.user_id = user_resp.json()["id"]
        vendor.save(update_fields=["user_id"])

        return Response(
            {"detail": "Vendor registered. Await admin approval."},
            status=200
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

        updated = VendorProfile.objects.filter(
            user_id=str(user_id),
            status="pending"
        ).update(status="approved")

        if updated == 0:
            return Response({"detail": "Vendor not found"}, status=404)

        return Response({"detail": "Vendor approved"}, status=200)