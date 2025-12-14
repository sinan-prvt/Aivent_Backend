import os
import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import VendorProfile, VendorApplicationOTP
from .serializers import VendorApplySerializer, VendorProfileSerializer
from .utils import create_vendor_otp_for, verify_vendor_otp
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import permissions
from .permissions import IsAdmin 
from django.utils import timezone
from vendor_app.tasks import send_email_task

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001/api/internal/users/")
AUTH_SERVICE_INTERNAL_TOKEN = os.getenv("AUTH_SERVICE_INTERNAL_TOKEN", None)

class VendorApplyView(APIView):
    permission_classes = [AllowAny]
     
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = VendorApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save(status="pending")

        raw_otp, otp_obj = create_vendor_otp_for(vendor)

        email = request.data.get("email")
        if email:
            send_email_task.delay(
                subject="AIVENT OTP Verification",
                message=f"Your OTP is: {raw_otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
        return Response({"message":"OTP sent to provided email","vendor_id": str(vendor.id)}, status=status.HTTP_201_CREATED)


class VerifyVendorOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        vendor_id = request.data.get("vendor_id")
        otp = request.data.get("otp")
        email = request.data.get("email")
        if not vendor_id or not otp or not email:
            return Response({"detail":"vendor_id, otp and email required"}, status=400)

        vendor = get_object_or_404(VendorProfile, id=vendor_id)
        otp_obj = VendorApplicationOTP.objects.filter(vendor=vendor, used=False, expires_at__gt=timezone.now()).order_by("-created_at").first()
        if not otp_obj:
            return Response({"detail":"OTP expired or not found"}, status=400)
        if not verify_vendor_otp(otp_obj, otp):
            return Response({"detail":"Invalid OTP"}, status=400)

        otp_obj.used = True
        otp_obj.save()

        payload = {
            "email": email,
            "role": "vendor",
            "email_verified": True,
            "is_active": False,
            "vendor_approved": False,
        }
        headers = {"Content-Type":"application/json"}
        if AUTH_SERVICE_INTERNAL_TOKEN:
            headers["Authorization"] = f"Bearer {AUTH_SERVICE_INTERNAL_TOKEN}"

        try:
            resp = requests.post(AUTH_SERVICE_URL.rstrip("/") + "/", json=payload, headers=headers, timeout=5)
            resp.raise_for_status()
        except requests.RequestException as e:
            return Response({"detail":"failed to create user in user-service", "error": str(e)}, status=502)

        created = resp.json()
        vendor.user_id = created.get("id") or created.get("user_id")
        vendor.save()

        return Response({"detail":"Vendor application confirmed. Await admin approval.", "user": created}, status=200)


class PendingVendorsView(generics.ListAPIView):
    serializer_class = VendorProfileSerializer
    # permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return VendorProfile.objects.filter(status="pending")

