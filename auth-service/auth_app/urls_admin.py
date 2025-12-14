# auth_app/urls_admin.py
from django.urls import path
from .views.admin import (
    AdminUserListView,
    AdminUserDetailView,
    AdminApproveVendorView,
    AdminRevokeTokensView,
    AdminMetricsView,
)

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("users/<int:user_id>/approve-vendor/", AdminApproveVendorView.as_view(), name="admin-approve-vendor"),
    path("users/<int:user_id>/revoke-tokens/", AdminRevokeTokensView.as_view(), name="admin-revoke-tokens"),
    path("metrics/", AdminMetricsView.as_view(), name="admin-metrics"),
]
