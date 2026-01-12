import uuid
from django.db import models

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Platform order_id (from core-service MasterOrder)
    order_id = models.UUIDField(unique=True, db_index=True)
    
    # Razorpay specific IDs
    razorpay_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("CREATED", "CREATED"),
            ("PAID", "PAID"),
            ("FAILED", "FAILED"),
        ],
        default="CREATED",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order {self.order_id} - {self.status}"
