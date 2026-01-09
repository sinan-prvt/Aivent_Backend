from rest_framework import generics, permissions
from catalog_app.models import Delivery
from catalog_app.serializers.delivery import DeliverySerializer
from catalog_app.permissions import IsVendor
from rest_framework.parsers import MultiPartParser, FormParser

class VendorDeliveryListCreateView(generics.ListCreateAPIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Delivery.objects.filter(vendor_id=self.request.user.id).order_by('-created_at')

class VendorDeliveryDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Delivery.objects.filter(vendor_id=self.request.user.id)
