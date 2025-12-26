from rest_framework import serializers
from .models import VendorProfile
from rest_framework import serializers
from .models import VendorProfile

class VendorApplySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "email",
            "password",
            "business_name",
            "category_id",
            "subcategory_ids",
            "phone",
            "address",
            "gst_number",
            "documents",
        ]
        read_only_fields = ("id",)



class VendorConfirmSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField()
    email = serializers.EmailField()
    otp = serializers.CharField()

    
class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = "__all__"
        read_only_fields = ("id","created_at","updated_at","user_id","status")
