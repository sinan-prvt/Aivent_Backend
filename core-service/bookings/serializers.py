from rest_framework import serializers
from .models import Booking
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated


class BookingCreateSerializer(serializers.ModelSerializer):
    permission_classes = [IsAuthenticated]
    
    class Meta:
        model = Booking
        fields = ["vendor_id", "event_date"]

    def create(self, validated_data):
        validated_data["expires_at"] = timezone.now() + timedelta(minutes=15)
        return super().create(validated_data)
