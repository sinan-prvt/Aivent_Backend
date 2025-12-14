from django.urls import path
from .views import (
    VendorApplyView,
    VerifyVendorOTPView,
    PendingVendorsView,
)

urlpatterns = [
    path("apply/", VendorApplyView.as_view(), name="vendor-apply"),
    path("verify-otp/", VerifyVendorOTPView.as_view(), name="vendor-verify-otp"),

    # Admin routes
    path("admin/vendors/pending/", PendingVendorsView.as_view(), name="pending-vendors"),
]
