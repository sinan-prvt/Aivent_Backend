from rest_framework import serializers
from orders.models import MasterOrder, SubOrder

class SubOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.SerializerMethodField()
    booking_status = serializers.SerializerMethodField()
    booking_details = serializers.SerializerMethodField()

    class Meta:
        model = SubOrder
        fields = ["id", "vendor_id", "vendor_name", "amount", "status", "booking_status", "created_at", "booking_details"]

    def get_vendor_name(self, obj):
        # In a real microservice, we might fetch this from vendor-service
        # For now, just return the ID or a placeholder
        return f"Vendor {obj.vendor_id}"

    def get_booking_status(self, obj):
        if hasattr(obj, "booking"):
            return obj.booking.status
        return "N/A"
    
    def get_booking_details(self, obj):
        if hasattr(obj, "booking"):
            return {
                "date": obj.booking.event_date,
                "guests": getattr(obj.booking, "guests", "N/A"),
                "product_title": "Product Details", # Placeholder
                "event_type": "Event" # Placeholder
            }
        return None

class MasterOrderSerializer(serializers.ModelSerializer):
    sub_orders = SubOrderSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = MasterOrder
        fields = ["id", "total_amount", "status", "created_at", "sub_orders", "item_count", "payment_order_id"]

    def get_item_count(self, obj):
        return obj.sub_orders.count()
