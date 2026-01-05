from rest_framework.generics import UpdateAPIView
from catalog_app.permissions import IsPlatformAdmin
from rest_framework.response import Response
from catalog_app.models import Product
from django.utils.timezone import now
from catalog_app.services.events import publish_catalog_event


class AdminApproveProductView(UpdateAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsPlatformAdmin]

    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        action = request.data.get("action")

        if action == "approve":
            product.status = Product.STATUS_APPROVED
            product.save()

            publish_catalog_event(
                event_type="PRODUCT_APPROVED",
                vendor_id=product.vendor_id,
                payload={
                    "product_id": product.id,
                    "name": product.name,
                }
            )

        elif action == "reject":
            product.status = Product.STATUS_REJECTED
            product.save()

            publish_catalog_event(
                event_type="PRODUCT_REJECTED",
                vendor_id=product.vendor_id,
                payload={
                    "product_id": product.id,
                    "name": product.name,
                }
            )

        else:
            return Response({"error": "Invalid action"}, status=400)

        return Response({"status": product.status})


from rest_framework.generics import ListAPIView
from catalog_app.serializers.product import AdminProductSerializer

class AdminProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = AdminProductSerializer
    permission_classes = [IsPlatformAdmin]

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')  # Show newest first
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset
