from rest_framework.generics import UpdateAPIView
from catalog_app.permissions import IsPlatformAdmin
from rest_framework.response import Response
from catalog_app.models import Product
from django.utils.timezone import now



class AdminApproveProductView(UpdateAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsPlatformAdmin]

    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        action = request.data.get("action")

        if action == "approve":
            product.status = Product.STATUS_APPROVED
            product.rejection_reason = None

        elif action == "reject":
            reason = request.data.get("reason")
            if not reason:
                return Response(
                    {"error": "Rejection reason required"},
                    status=400
                )
            product.status = Product.STATUS_REJECTED
            product.rejection_reason = reason

        else:
            return Response({"error": "Invalid action"}, status=400)

        product.reviewed_at = now()
        product.reviewed_by = request.user.id
        product.save()

        return Response({
            "status": product.status,
            "reviewed_at": product.reviewed_at,
            "rejection_reason": product.rejection_reason
        })