import uuid
from django.db import models

class MasterOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.PositiveIntegerField(db_index=True)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "PENDING"),
            ("AWAITING_APPROVAL", "AWAITING_APPROVAL"),
            ("PARTIALLY_APPROVED", "PARTIALLY_APPROVED"),
            ("PAID", "PAID"),
            ("FAILED", "FAILED"),
        ],
        default="PENDING",
    )
    
    # Razorpay order_id from payment-service will link here later
    payment_order_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} for User {self.user_id}"


class SubOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    master_order = models.ForeignKey(MasterOrder, related_name="sub_orders", on_delete=models.CASCADE)
    
    vendor_id = models.UUIDField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "PENDING"),
            ("PAID", "PAID"),
            ("COMPLETED", "COMPLETED"),
            ("CANCELLED", "CANCELLED"),
        ],
        default="PENDING",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SubOrder {self.id} for Vendor {self.vendor_id}"
