from rest_framework.generics import ListCreateAPIView
from catalog_app.permissions import IsVendor
from catalog_app.models import Product
from catalog_app.serializers.product import VendorProductSerializer,ProductSerializer
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import PermissionDenied

class VendorProductListCreateView(ListCreateAPIView):
    serializer_class = VendorProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(
            vendor_id=self.request.user.id,
            status=Product.STATUS_PENDING
        )

class VendorProductDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        # Vendor can access ONLY their own products
        return Product.objects.filter(vendor_id=self.request.user.id)