# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.contrib.auth import get_user_model
# from rest_framework import status
# import os

# User = get_user_model()

# INTERNAL_TOKEN = os.getenv("AUTH_SERVICE_INTERNAL_TOKEN")

# class InternalVendorApprove(APIView):
#     def patch(self, request):
#         if request.headers.get("X-Internal-Token") != INTERNAL_TOKEN:
#             return Response({"detail": "Forbidden"}, status=403)

#         user_id = request.data.get("user_id")
#         if not user_id:
#             return Response({"detail": "user_id required"}, status=400)

#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({"detail": "User not found"}, status=404)

#         user.vendor_approved = True
#         user.is_active = True
#         user.save(update_fields=["vendor_approved", "is_active"])

#         return Response({"message": "Vendor approved"}, status=200)
