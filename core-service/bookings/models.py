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
    vendor_id = models.CharField(max_length=100)
    vendor_name = models.CharField(max_length=255, default="Aivent Partner")
    product_name = models.CharField(max_length=255, default="Event Service")
    category_name = models.CharField(max_length=100, default="Service")
    event_type = models.CharField(max_length=100, default="Event")
    guests = models.CharField(max_length=50, default="N/A")
    event_date = models.DateField()
    
    # Link to SubOrder in orders app
    sub_order = models.OneToOneField(
        'orders.SubOrder', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="booking"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("HOLD", "HOLD"),
            ("AWAITING_APPROVAL", "AWAITING_APPROVAL"),
            ("APPROVED", "APPROVED"),
            ("REJECTED", "REJECTED"),
            ("CONFIRMED", "CONFIRMED"),
            ("CANCELLED", "CANCELLED"),
        ],
        default="AWAITING_APPROVAL",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor_id", "event_date"],
                condition=models.Q(status__in=["HOLD", "CONFIRMED"]),
                name="unique_active_booking"
            )
        ]

    def confirm(self):
        if self.status not in ["HOLD", "APPROVED"]:
            raise ValidationError(f"Cannot confirm booking in {self.status} status")
        self.status = "CONFIRMED"
        self.save(update_fields=["status"])

    def cancel(self, reason="system"):
        if self.status == "CANCELLED":
            return
        self.status = "CANCELLED"
        self.save(update_fields=["status"])



class IdempotencyKey(models.Model):
    key = models.CharField(max_length=100)
    user_id = models.PositiveIntegerField()
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "user_id"],
                name="unique_idempotency_per_user"
            )
        ]
