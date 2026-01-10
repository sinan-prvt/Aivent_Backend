from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor_id", "event_date", "status", "expires_at")
    list_filter = ("status", "event_date")