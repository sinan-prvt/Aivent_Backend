from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers import VendorRegisterSerializer
from auth_app.tasks import send_email_task

class VendorRegisterView(APIView):
    def post(self, request):
        serializer = VendorRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, raw_otp = serializer.save()

        send_email_task.delay(
            subject="AIVENT Vendor Registration OTP",
            message=f"Your OTP is: {raw_otp}",
            recipient_list=[user.email]
        )

        return Response({
            "message": "OTP sent to email",
            "user_id": str(user.id)
        })
