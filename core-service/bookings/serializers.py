from rest_framework import serializers
from .models import Booking
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated


class BookingCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Booking
        fields = ["vendor_id", "event_date"]
