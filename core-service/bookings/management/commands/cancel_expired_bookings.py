# bookings/management/commands/cancel_expired_bookings.py
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from bookings.models import Booking

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        expired = Booking.objects.filter(
            status="HOLD",
            expires_at__lt=now()
        )
        for booking in expired:
            booking.cancel(reason="expired")
