import uuid
from django.db import models


class VendorProfile(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField(blank=True, null=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    category_id = models.IntegerField(null=True, blank=True)
    subcategory_ids = models.JSONField(default=list, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gst_number = models.CharField(max_length=64, blank=True, null=True)
    documents = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(status="pending"),
                name="unique_pending_vendor_per_email",
            )
        ]

    def __str__(self):
        return f"{self.business_name} ({self.id})"


class Notification(models.Model):
    vendor_id = models.BigIntegerField(db_index=True)

    event_id = models.UUIDField(unique=True, db_index=True)
    event_type = models.CharField(max_length=100)

    title = models.CharField(max_length=255)
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification(event={self.event_id}, vendor={self.vendor_id})"