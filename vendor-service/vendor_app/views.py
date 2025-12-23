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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from django.db import transaction
from rest_framework.throttling import AnonRateThrottle


logger = logging.getLogger(__name__)



@method_decorator(csrf_exempt, name="dispatch")
class VendorApplyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VendorApplySerializer(data=request.data)

        if not serializer.is_valid():
            print("SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

        vendor = serializer.save()

        raw_otp, _ = create_vendor_otp_for(vendor)

        email = request.data.get("email")
        if email:
            try:
                send_email_task.delay(
                    subject="AIVENT OTP Verification",
                    message=f"Your OTP is: {raw_otp}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
            except Exception:
                return Response({"detail": "Failed to send OTP email"}, status=500)


        return Response(
            {
                "message": "OTP sent to provided email",
                "vendor_id": str(vendor.id),
            },
            status=status.HTTP_201_CREATED,
        )

class VerifyVendorOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        vendor_id = request.data.get("vendor_id")
        otp = request.data.get("otp")
        email = request.data.get("email")

        if not vendor_id or not otp or not email:
            return Response(
                {"detail": "vendor_id, otp and email required"},
                status=400
            )

        vendor = get_object_or_404(VendorProfile, id=vendor_id)

        otp_obj = VendorApplicationOTP.objects.filter(
            vendor=vendor,
            used=False,
            expires_at__gt=timezone.now()
        ).order_by("-created_at").first()

        if not otp_obj:
            return Response({"detail": "OTP expired or not found"}, status=400)

        if vendor.email != email:
            return Response({"detail": "Email mismatch"}, status=400)

        if not verify_vendor_otp(otp_obj, otp):
            return Response({"detail": "Invalid OTP"}, status=400)

        payload = {
            "email": email,
            "role": "vendor",
        }

        headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN,
            "Host": "auth-service",
        }

        auth_url = f"{settings.AUTH_SERVICE_INTERNAL_URL}/api/auth/internal/users/"

        try:
            with transaction.atomic():
                resp = requests.post(auth_url, json=payload, headers=headers, timeout=5)
                if resp.status_code == 409:
                    return Response(
                        {"detail": "Vendor user already exists"},
                        status=400
                    )

                resp.raise_for_status()

                vendor.user_id = resp.json()["id"]
                vendor.save(update_fields=["user_id"])

        except requests.RequestException as e:
            return Response(
                {"detail": "auth-service failed", "error": str(e)},
                status=502
            )

        return Response(
            {"detail": "Vendor application confirmed. Await admin approval."},
            status=200
        )



class PendingVendorsView(generics.ListAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return VendorProfile.objects.filter(status="pending")

