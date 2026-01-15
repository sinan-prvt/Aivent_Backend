from rest_framework import serializers
from orders.models import MasterOrder, SubOrder

class SubOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.SerializerMethodField()
    booking_status = serializers.SerializerMethodField()
    booking_details = serializers.SerializerMethodField()
    booking_id = serializers.SerializerMethodField()
    booking_user_id = serializers.SerializerMethodField()

    class Meta:
        model = SubOrder
        fields = ["id", "vendor_id", "vendor_name", "amount", "status", "booking_status", "booking_id", "booking_user_id", "created_at", "booking_details"]

    def get_vendor_name(self, obj):
        if hasattr(obj, "booking"):
            return obj.booking.vendor_name
        return "Aivent Partner"

    def get_booking_user_id(self, obj):
        # MasterOrder has the user_id
        return obj.master_order.user_id

    def get_booking_status(self, obj):
        if hasattr(obj, "booking"):
            return obj.booking.status
        return "N/A"

    def get_booking_id(self, obj):
        if hasattr(obj, "booking"):
            return str(obj.booking.id)
        return None
    
    def get_booking_details(self, obj):
        if hasattr(obj, "booking"):
            return {
                "date": obj.booking.event_date,
                "guests": obj.booking.guests,
                "product_title": obj.booking.product_name,
                "event_type": obj.booking.event_type,
                "category_name": obj.booking.category_name,
                "customer_name": obj.booking.customer_name,
                "customer_email": obj.booking.customer_email,
                "customer_phone": obj.booking.customer_phone,
                "customer_address": obj.booking.customer_address,
                "customer_city": obj.booking.customer_city,
                "customer_notes": obj.booking.customer_notes
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
