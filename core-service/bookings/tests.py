import pytest
from django.utils import timezone
from .models import Booking

@pytest.mark.django_db
class TestBookingModel:
    def test_create_booking(self):
        booking = Booking.objects.create(
            user_id=1,
            vendor_id="vendor_123",
            event_date=timezone.now().date(),
        )
        assert booking.status == "AWAITING_APPROVAL"
        assert booking.vendor_name == "Aivent Partner"

    def test_confirm_booking(self):
        booking = Booking.objects.create(
            user_id=1,
            vendor_id="vendor_123",
            event_date=timezone.now().date(),
            status="APPROVED"
        )
        booking.confirm()
        assert booking.status == "CONFIRMED"
