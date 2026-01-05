import os
import requests
from django.conf import settings
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import VendorProfile, Notification
from .serializers import VendorApplySerializer, VendorProfileSerializer, VendorConfirmSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from vendor_app.permissions import IsAdmin 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from django.db import transaction
from rest_framework.generics import ListAPIView
import sys
from rest_framework.exceptions import PermissionDenied
from .serializers import NotificationSerializer
from rest_framework import status

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

        password = serializer.validated_data.pop("password")
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

        user_resp = requests.post(
            f"{settings.AUTH_SERVICE_URL}/internal/users/",
            json={"email": email, "password": password, "role": "vendor"},
            headers={"X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN},
            timeout=5,
        )

        if user_resp.status_code not in (200, 201, 409):
            raise RuntimeError("Auth service user creation failed")

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
    

class VendorNotificationListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        vendor_id = self.request.user.id  # or vendor_profile.user_id
        qs = Notification.objects.filter(vendor_id=vendor_id)

        unread = self.request.query_params.get("unread")
        if unread == "true":
            qs = qs.filter(is_read=False)

        return qs


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        vendor_id = request.user.id

        notification = get_object_or_404(
            Notification,
            id=pk,
            vendor_id=vendor_id
        )

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class UnreadNotificationCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendor_id = request.user.id

        count = Notification.objects.filter(
            vendor_id=vendor_id,
            is_read=False
        ).count()

        return Response({"unread_count": count})


class VendorMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"🔍 VendorMeView: Request User: {request.user}", flush=True)
        print(f"🔍 VendorMeView: Request User ID: {request.user.id}", flush=True)
        
        try:
            vendor = VendorProfile.objects.get(user_id=request.user.id)
            print(f"🔍 VendorMeView: Found Profile: {vendor.id} for User ID: {request.user.id}", flush=True)
        except VendorProfile.DoesNotExist:
            print(f"🔍 VendorMeView: ❌ Profile NOT FOUND for User ID: {request.user.id}", flush=True)
            # print all profiles to see if any exist
            all_profiles = VendorProfile.objects.all().values('id', 'user_id', 'email')
            print(f"🔍 VendorMeView: Dump specific profiles: {list(all_profiles)}", flush=True)
            return Response({"detail": "Vendor profile not found"}, status=404)

        serializer = VendorProfileSerializer(vendor)
        return Response(serializer.data)


class PublicVendorDetailView(generics.RetrieveAPIView):
    """
    Public endpoint to get vendor details by their user_id.
    """
    serializer_class = VendorProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = "user_id"
    queryset = VendorProfile.objects.filter(status="approved") # Only approved vendors
