from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework import status
import os

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")

User = get_user_model()

class InternalVendorApprove(APIView):
    def patch(self, request):
        if request.headers.get("X-INTERNAL-SECRET") != INTERNAL_SECRET:
            return Response({"detail": "Forbidden"}, status=403)

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        user.vendor_approved = True
        user.save()

        return Response({"message": "Vendor approved"})
