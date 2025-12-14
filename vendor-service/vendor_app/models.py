import uuid
from django.db import models
from django.utils import timezone

class VendorProfile(models.Model):
    STATUS_CHOICES = [
        ("pending","Pending"),
        ("approved","Approved"),
        ("rejected","Rejected"),
        ("suspended","Suspended"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    business_name = models.CharField(max_length=255)
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
        indexes = [
            models.Index(fields=("user_id",)),
            models.Index(fields=("status",)),
        ]

    def __str__(self):
        return f"{self.business_name} ({self.id})"
    

class VendorApplicationOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name="otps")
    otp_hash = models.CharField(max_length=128)
    salt = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at
