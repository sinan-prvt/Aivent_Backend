from celery import shared_task
import logging
from core.rabbit import publish_event
from django.utils import timezone
from bookings.models import Booking

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def publish_event_task(self, routing_key, payload):
    try:
        publish_event(routing_key, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task
def cleanup_expired_bookings():
    expired = Booking.objects.filter(
        status="HOLD",
        expires_at__lte=timezone.now()
    )
    count = expired.count()
    if count > 0:
        logger.info(f"Cleaning up {count} expired bookings")
        for booking in expired:
            booking.cancel(reason="expiry")
    return f"Cancelled {count} bookings"
