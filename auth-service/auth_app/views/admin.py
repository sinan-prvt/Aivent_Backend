from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, filters
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from user_app.permissions import IsAdmin
from ..serializers import AdminUserSerializer, AdminUserUpdateSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.conf import settings
import requests

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUserSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "username", "full_name", "phone"]
    ordering_fields = ["date_joined", "email", "username"]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        role = self.request.query_params.get("role")
        pending_vendor = self.request.query_params.get("pending_vendor")
        if role:
            qs = qs.filter(role=role)
        if pending_vendor and pending_vendor.lower() in ("1", "true", "yes"):
            qs = qs.filter(role="vendor", vendor_approved=False)
        return qs


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminUserSerializer(user)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
        )

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            AdminUserSerializer(user).data, 
            status=status.HTTP_200_OK
        )

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(
            {"detail": "User deactivated"}, 
            status=status.HTTP_200_OK
        )


class AdminApproveVendorView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        user = User.objects.filter(id=user_id, role="vendor").first()
        if not user:
            return Response(
                {"detail": "Vendor not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get("action", "approve")

        if action != "approve":
            return Response(
                {"detail": "Only approve supported"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user.vendor_approved = True
        user.is_active = True
        user.save(update_fields=["vendor_approved", "is_active"])

        resp = requests.patch(
            f"{settings.VENDOR_SERVICE_URL}/api/vendors/internal/vendors/approve/",
            json={"user_id": str(user.id)},
            headers={
                "X-Internal-Token": settings.AUTH_SERVICE_INTERNAL_TOKEN
            },
            timeout=5,
        )

        if resp.status_code != 200:
            return Response(
                {
                    "detail": "Auth approved, vendor-service failed",
                    "vendor_service_response": resp.text,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"detail": "Vendor approved successfully"}, 
            status=status.HTTP_200_OK
        )


class AdminRevokeTokensView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        tokens = OutstandingToken.objects.filter(user=user)
        count = 0
        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)
            count += 1
        return Response(
            {"detail": "Tokens revoked", "revoked_count": count}, 
            status=status.HTTP_200_OK
        )


class AdminMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response(
            {
                "total_users": User.objects.count(),
                "total_vendors": User.objects.filter(role="vendor").count(),
                "awaiting_vendor_approval": User.objects.filter(
                    role="vendor", vendor_approved=False
                ).count(),
                "active_users": User.objects.filter(is_active=True).count(),
            },
            status=status.HTTP_200_OK,
        )
    
