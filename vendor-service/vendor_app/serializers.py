from rest_framework import serializers
from .models import VendorProfile

class VendorApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "business_name",
            "category_id",
            "subcategory_ids",
            "phone",
            "address",
            "gst_number",
            "documents",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id","status","created_at","updated_at")

class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = "__all__"
        read_only_fields = ("id","created_at","updated_at","user_id","status")
