from django.urls import path
from .views import (
    VendorApplyView,
    PendingVendorsView,
    VendorConfirmView,
    InternalVendorApproveView,
    VendorNotificationListView,
    UnreadNotificationCountView,
    MarkNotificationReadView,
)

urlpatterns = [
    path("apply/", VendorApplyView.as_view(), name="vendor-apply"),
    path("confirm/", VendorConfirmView.as_view(), name="vendor-confirm"),

    path("admin/vendors/pending/", PendingVendorsView.as_view(), name="pending-vendors"),
    path("internal/vendors/approve/", InternalVendorApproveView.as_view(), name="internal-vendor-approve",),

    path("notifications/", VendorNotificationListView.as_view()),
    path("notifications/unread-count/", UnreadNotificationCountView.as_view()),
    path("notifications/<int:pk>/read/", MarkNotificationReadView.as_view()),
]
