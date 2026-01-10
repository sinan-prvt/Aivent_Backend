from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta



def default_expiry():
    return timezone.now() + timedelta(minutes=15)


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.PositiveIntegerField()
    vendor_id = models.UUIDField()

    event_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("HOLD", "HOLD"),
            ("CONFIRMED", "CONFIRMED"),
            ("CANCELLED", "CANCELLED"),
        ],
        default="HOLD",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor_id", "event_date"],
                name="unique_vendor_event_date"
            )
        ]