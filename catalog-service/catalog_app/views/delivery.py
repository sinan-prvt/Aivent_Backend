from rest_framework import generics, permissions
from catalog_app.models import Delivery
from catalog_app.serializers.delivery import DeliverySerializer
from catalog_app.permissions import IsVendor

class VendorDeliveryListCreateView(generics.ListCreateAPIView):
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Delivery.objects.filter(vendor_id=self.request.user.id).order_by('-created_at')

class VendorDeliveryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Delivery.objects.filter(vendor_id=self.request.user.id)
