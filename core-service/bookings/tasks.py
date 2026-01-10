from celery import shared_task
from django.utils import timezone
from bookings.models import Booking
from core.tasks import publish_event_task  # reuse infra task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def expire_hold_bookings(self):
    now = timezone.now()

    expired = (
        Booking.objects
        .filter(status=Booking.Status.HOLD, expires_at__lt=now)
    )

    count = expired.count()
    if count == 0:
        return {"expired": 0}

    for booking in expired:
        booking.status = Booking.Status.EXPIRED
        booking.save(update_fields=["status"])

        publish_event_task.delay(
            routing_key="booking.expired",
            payload={
                "booking_id": str(booking.id),
                "vendor_id": str(booking.vendor_id),
                "event_date": str(booking.event_date),
            }
        )

    logger.info("Expired %s bookings", count)
    return {"expired": count}
