from rest_framework import serializers
from catalog_app.models import Category


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "children"]

    def get_children(self, obj):
        return CategorySerializer(
            obj.children.filter(is_active=True),
            many=True
        ).data