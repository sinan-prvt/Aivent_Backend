from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from ..serializers import (
    ResetPasswordSerializer
)
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from ..models import OTP


User = get_user_model()


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Reset password using verified OTP",
        tags=["Password Reset"]
    )

    def post(self, request):
        serializers = ResetPasswordSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)

        email = serializers.validated_data["email"]
        new_password = serializers.validated_data["new_password"]

        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        otp_obj = OTP.objects.filter(
            user=user, 
            purpose="reset_password", 
            used=True
        ).order_by("-created_at").first()

        if not otp_obj:
            return Response({"detail": "OTP not verified"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password reset successful"}, status=status.HTTP_200_OK)

