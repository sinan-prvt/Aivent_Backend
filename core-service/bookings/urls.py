
from django.urls import path
from .views import BookingCreateAPIView, BookingConfirmAPIView, VendorBookingApprovalAPIView, VendorBookingRejectionAPIView

urlpatterns = [
    path("", BookingCreateAPIView.as_view(), name="create-booking"),
    path("<uuid:booking_id>/confirm/", BookingConfirmAPIView.as_view(), name="confirm-booking"),
    # Vendor Actions
    path("<uuid:booking_id>/approve/", VendorBookingApprovalAPIView.as_view(), name="approve-booking"),
    path("<uuid:booking_id>/reject/", VendorBookingRejectionAPIView.as_view(), name="reject-booking"),
]