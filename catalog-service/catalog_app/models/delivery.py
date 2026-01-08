from django.db import models

class Delivery(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_UPLOADING = "uploading"
    STATUS_DELIVERED = "delivered"
    STATUS_PENDING = "pending"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_UPLOADING, "Uploading"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_PENDING, "Pending"),
    ]

    vendor_id = models.IntegerField(db_index=True)
    client_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=255)
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    progress = models.IntegerField(default=0)
    thumbnail = models.ImageField(upload_to="deliveries/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_name} - {self.event_type}"
