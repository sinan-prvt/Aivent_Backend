from django.urls import path
from .views import BookingCreateAPIView

urlpatterns = [
    path("", BookingCreateAPIView.as_view(), name="create-booking"),
]
