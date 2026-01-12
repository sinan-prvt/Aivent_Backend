from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from orders.models import MasterOrder
from bookings.models import Booking

class PaymentSuccessAPIView(APIView):
    def post(self, request):
        master_order_id = request.data.get("order_id")

        if not master_order_id:
            return Response(
                {"detail": "order_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                master_order = MasterOrder.objects.select_for_update().get(
                    id=master_order_id
                )

                # 1. Mark master order PAID
                master_order.status = "PAID"
                master_order.save(update_fields=["status"])

                # 2. Mark all sub-orders PAID
                for sub in master_order.sub_orders.all():
                    sub.status = "PAID"
                    sub.save(update_fields=["status"])

                    # 3. Confirm booking linked to sub-order
                    if hasattr(sub, "booking"):
                        sub.booking.confirm()

        except MasterOrder.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"status": "ORDER_CONFIRMED"},
            status=status.HTTP_200_OK
        )
