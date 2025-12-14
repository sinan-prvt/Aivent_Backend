from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from auth_app.models import OTP
from auth_app.tasks import publish_event_task
from auth_app.utils import make_otp_hash
from auth_app.utils import verify_otp_entry


User = get_user_model()

class VendorVerifyOTPView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        otp = request.data.get("otp")

        if not user_id or not otp:
            return Response({"detail": "user_id and otp required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "user not found"}, status=404)

        # Get latest vendor_register OTP
        otp_obj = (
            OTP.objects.filter(
                user=user,
                purpose="vendor_register",
                used=False,
                expires_at__gt=timezone.now()
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_obj:
            return Response({"detail": "OTP expired or not found"}, status=400)

        # Check hash
        if not verify_otp_entry(otp_obj, otp):
            return Response({"detail": "Invalid OTP"}, status=400)  


        # Publish event for vendor-service
        publish_event_task.delay(
            "vendor.created",
            {
                "event": "USER_VENDOR_CREATED",
                "user_id": str(user.id),
                "email": user.email,
                "phone": user.phone,
            }
        )

        return Response({
            "message": "Vendor registered. Waiting for admin approval."
        })