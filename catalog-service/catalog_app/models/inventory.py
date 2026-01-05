from django.db import models

class InventoryItem(models.Model):
    CONDITION_CHOICES = [
        ("pristine", "Pristine"),
        ("excellent", "Excellent"),
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
    ]

    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=255)  # e.g., "Mandap Decoration"
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default="good")
    vendor_id = models.IntegerField(db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity})"

class InventoryImage(models.Model):
    item = models.ForeignKey(InventoryItem, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='inventory/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.item.name}"
