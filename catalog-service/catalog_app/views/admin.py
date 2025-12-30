from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from catalog_app.models import Product


class AdminApproveProductView(UpdateAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAdminUser]

    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        action = request.data.get("action")

        if action == "approve":
            product.status = Product.STATUS_APPROVED
        elif action == "reject":
            product.status = Product.STATUS_REJECTED
        else:
            return Response({"error": "Invalid action"}, status=400)

        product.save()
        return Response({"status": product.status})
