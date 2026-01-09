from rest_framework import serializers
from catalog_app.models import Product, ProductImage


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 
                 'vendor_id', 'city', 'status', 'is_available', 'stock', 
                 'image', 'created_at', 'features']
        read_only_fields = ['vendor_id', 'status', 'created_at']
    
    def to_internal_value(self, data):
        # Handle features being sent as a JSON string (common with FormData/MultiPartParser)
        try:
            if 'features' in data and isinstance(data['features'], (str, bytes)):
                import json
                # Create a mutable copy if it's a QueryDict
                if hasattr(data, 'copy'):
                    data = data.copy()
                data['features'] = json.loads(data['features'])
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        return super().to_internal_value(data)

class PublicProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "image", "category", "vendor_id", "city", "stock"]

class VendorProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "image",
            "stock",
            "status",
            "features",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]

    def to_internal_value(self, data):
        # Handle features being sent as a JSON string
        try:
            if 'features' in data and isinstance(data['features'], (str, bytes)):
                import json
                if hasattr(data, 'copy'):
                    data = data.copy()
                data['features'] = json.loads(data['features'])
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        return super().to_internal_value(data)


class VendorProductUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "category",
            "image",
            "stock",
            "features",
            "is_available",
        ]

    def to_internal_value(self, data):
        try:
            if 'features' in data and isinstance(data['features'], (str, bytes)):
                import json
                if hasattr(data, 'copy'):
                    data = data.copy()
                data['features'] = json.loads(data['features'])
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        return super().to_internal_value(data)


class AdminProductSerializer(serializers.ModelSerializer):
    """
    Serializer for admin product list and review
    """
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "vendor_id",
            "city",
            "image",
            "stock",
            "status",
            "is_available",
            "created_at",
            "updated_at",
        ]
