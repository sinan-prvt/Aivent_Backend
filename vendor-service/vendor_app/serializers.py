from rest_framework import serializers
from .models import VendorProfile
from rest_framework import serializers
from .models import VendorProfile

class VendorApplySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

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
            "email",
        ]
        read_only_fields = ("id",)

    def create(self, validated_data):
        return VendorProfile.objects.create(**validated_data)



class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = "__all__"
        read_only_fields = ("id","created_at","updated_at","user_id","status")
