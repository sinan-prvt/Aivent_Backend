from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from core.authentication import StatelessJWTAuthentication
from core.permissions import HasValidJWT
from orders.models import MasterOrder, SubOrder
from bookings.models import Booking
from orders.serializers import MasterOrderSerializer, SubOrderSerializer
from django.shortcuts import get_object_or_404

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

class UserOrderListAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def get(self, request):
        user_id = request.auth["user_id"]
        orders = MasterOrder.objects.filter(user_id=user_id).order_by("-created_at")
        serializer = MasterOrderSerializer(orders, many=True)
        return Response(serializer.data)

class VendorOrderListAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def get(self, request):
        if request.auth.get("role") != "vendor" and request.auth.get("role") != "admin":
             return Response({"detail": "Vendor access required"}, status=403)

        vendor_id = request.query_params.get("vendor_id")
        if not vendor_id:
             return Response([])

        orders = SubOrder.objects.filter(vendor_id=vendor_id).order_by("-created_at")
        serializer = SubOrderSerializer(orders, many=True)
        return Response(serializer.data)

class AdminOrderListAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def get(self, request):
        if request.auth.get("role") != "admin":
            return Response({"detail": "Admin access required"}, status=403)
            
        orders = MasterOrder.objects.all().order_by("-created_at")
        serializer = MasterOrderSerializer(orders, many=True)
        return Response(serializer.data)

class AdminOrderUpdateAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def patch(self, request, order_id):
        if request.auth.get("role") != "admin":
            return Response({"detail": "Admin access required"}, status=403)
        
        order = get_object_or_404(MasterOrder, id=order_id)
        status_val = request.data.get("status")
        
        if status_val:
            order.status = status_val
            order.save()
            
            if status_val == "PAID":
                for sub in order.sub_orders.all():
                    sub.status = "PAID"
                    sub.save()
                    if hasattr(sub, "booking"):
                        sub.booking.confirm()
            
        return Response(MasterOrderSerializer(order).data)

class SubOrderDeleteAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def delete(self, request, sub_order_id):
        user_id = request.auth["user_id"]
        
        # Ensure the sub_order belongs to a master_order owned by the user
        sub_order = get_object_or_404(SubOrder, id=sub_order_id, master_order__user_id=user_id)
        
        with transaction.atomic():
            master_order = sub_order.master_order
            
            # Reduce total amount
            # Only if not already cancelled? Amount is always there.
            if sub_order.status != "CANCELLED":
                 master_order.total_amount -= sub_order.amount
            
            # Delete booking if exists
            if hasattr(sub_order, 'booking'):
                sub_order.booking.delete()
            
            sub_order.delete()
            master_order.save()
            
            # If no items left, maybe delete master order? or just leave empty?
            if master_order.sub_orders.count() == 0:
                master_order.delete()
                return Response({"status": "Order Deleted as empty"}, status=200)

            # Re-evaluate status
            # Re-evaluate status
            from orders.services import update_master_order_status
            update_master_order_status(master_order)

        return Response({"status": "Item Removed"}, status=200)

class OrderDetailAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def get(self, request, order_id):
        user_id = request.auth["user_id"]
        order = get_object_or_404(MasterOrder, id=order_id, user_id=user_id)
        return Response(MasterOrderSerializer(order).data)
