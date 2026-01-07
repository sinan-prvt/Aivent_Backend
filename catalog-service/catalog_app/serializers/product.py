from rest_framework import serializers
from catalog_app.models import Product, ProductImage


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 
                 'vendor_id', 'status', 'is_available', 'stock', 
                 'image', 'created_at', 'features']
        read_only_fields = ['vendor_id', 'status', 'created_at']

class PublicProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "image", "category", "vendor_id", "stock"]

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status"]


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
            "is_available",
        ]


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
            "image",
            "stock",
            "status",
            "is_available",
            "created_at",
            "updated_at",
        ]
