from django.urls import path
from .views import BookingCreateAPIView, BookingConfirmAPIView

urlpatterns = [
    path("", BookingCreateAPIView.as_view(), name="create-booking"),
    path("<uuid:booking_id>/confirm/", BookingConfirmAPIView.as_view(), name="confirm-booking"),
]