import uuid
from django.db import models


class ChatMessage(models.Model):
    CUSTOMER = "customer"
    VENDOR = "vendor"

    SENDER_CHOICES = [
        (CUSTOMER, "Customer"),
        (VENDOR, "Vendor"),
    ]

    message_id = models.UUIDField(unique=True, db_index=True)

    user_id = models.IntegerField()
    vendor_id = models.IntegerField()

    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)

    message = models.TextField()

    # 🔹 NEW FIELD
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user_id", "vendor_id"]),
            models.Index(fields=["vendor_id", "is_read"]),
        ]
