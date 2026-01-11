from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


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

    def confirm(self):
        if self.status != "HOLD":
            raise ValidationError("Only HOLD bookings can be confirmed")
        self.status = "CONFIRMED"
        self.save(update_fields=["status"])

    def cancel(self, reason="system"):
        if self.status != "HOLD":
            raise ValidationError("Only HOLD bookings can be cancelled")
        self.status = "CANCELLED"
        self.save(update_fields=["status"])



class IdempotencyKey(models.Model):
    key = models.CharField(max_length=100, unique=True)
    user_id = models.PositiveIntegerField()
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)