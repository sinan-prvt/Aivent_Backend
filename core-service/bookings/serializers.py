from rest_framework import serializers
from .models import Booking
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated


class BookingCreateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, write_only=True)
    
    class Meta:
        model = Booking
        fields = [
            "vendor_id", "vendor_name", "product_name", 
            "category_name", "event_type", "guests", 
            "event_date", "amount", "sub_order",
            "customer_name", "customer_email", "customer_phone", 
            "customer_address", "customer_city", "customer_notes"
        ]
        read_only_fields = ["sub_order"]
