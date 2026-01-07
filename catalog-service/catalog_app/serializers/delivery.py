from rest_framework import serializers
from catalog_app.models import Delivery

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'
        read_only_fields = ['vendor_id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['vendor_id'] = user.id
        return super().create(validated_data)
