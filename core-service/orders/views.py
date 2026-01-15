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
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        import logging
        from django.core.exceptions import ObjectDoesNotExist, ValidationError
        logger = logging.getLogger(__name__)
        master_order_id = request.data.get("order_id")
        logger.info(f"Received payment success notification for order: {master_order_id}")

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
                    try:
                        # Accessing reverse OneToOne can raise ObjectDoesNotExist
                        booking = sub.booking
                        booking.confirm()
                    except ObjectDoesNotExist:
                        logger.warning(f"SubOrder {sub.id} has no linked booking to confirm.")
                    except ValidationError as e:
                        logger.error(f"Cannot confirm booking {sub.booking.id if hasattr(sub, 'booking') else '?'}: {e}")
                        # Optionally force update status if needed, but logging is crucial
                    except Exception as e:
                        logger.error(f"Unexpected error confirming booking for sub_order {sub.id}: {e}")

        except MasterOrder.DoesNotExist:
            return Response(
                {"detail": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"status": "ORDER_CONFIRMED"},
            status=status.HTTP_200_OK
        )

# In-memory cache for vendor names to avoid repeated internal API calls
VENDOR_NAME_CACHE = {}

def resolve_vendor_name(sub_order):
    """
    Attempts to resolve vendor name from vendor-service if it's the default placeholder.
    Vendor name is stored on the linked Booking object.
    """
    if not hasattr(sub_order, 'booking') or not sub_order.booking:
        return None

    booking = sub_order.booking
    if booking.vendor_name != "Aivent Partner" and booking.vendor_name:
        return booking.vendor_name
        
    global VENDOR_NAME_CACHE
    vid = str(sub_order.vendor_id)
    
    if vid in VENDOR_NAME_CACHE:
        if VENDOR_NAME_CACHE[vid] and VENDOR_NAME_CACHE[vid] != booking.vendor_name:
            booking.vendor_name = VENDOR_NAME_CACHE[vid]
            booking.save(update_fields=["vendor_name"])
        return VENDOR_NAME_CACHE[vid]

    import requests
    from django.conf import settings
        
    try:
        url = f"{settings.VENDOR_SERVICE_URL}/public/vendors/{vid}/"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            business_name = data.get("business_name") or data.get("name")
            if business_name:
                booking.vendor_name = business_name
                booking.save(update_fields=["vendor_name"])
                
                # Update cache
                VENDOR_NAME_CACHE[vid] = business_name
                return business_name
    except Exception as e:
        print(f"Error resolving vendor name for {vid}: {e}")
        # Mark as failed in cache for the lifecycle of this process to avoid spamming
        VENDOR_NAME_CACHE[vid] = booking.vendor_name
        
    return booking.vendor_name

class UserOrderListAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def get(self, request):
        user_id = request.auth["user_id"]
        orders = MasterOrder.objects.filter(user_id=user_id).order_by("-created_at")
        
        # Self-healing: Sync totals for legacy orders
        from django.db.models import Sum
        for order in orders:
            actual_total = order.sub_orders.exclude(status="CANCELLED").aggregate(Sum('amount'))['amount__sum'] or 0
            if order.total_amount != actual_total:
                order.total_amount = actual_total
                order.save(update_fields=['total_amount'])
            
            # Sync vendor names
            for sub in order.sub_orders.all():
                resolve_vendor_name(sub)

        serializer = MasterOrderSerializer(orders, many=True)
        return Response(serializer.data)

class VendorOrderListAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def get(self, request):
        if request.auth.get("role") != "vendor" and request.auth.get("role") != "admin":
             return Response({"detail": "Vendor access required"}, status=403)

        # Use the authenticated user's ID as the vendor_id
        # Convert to string because vendor_id is now a CharField
        vendor_id = str(request.auth.get("user_id"))
        
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

    def delete(self, request, order_id, sub_order_id):
        user_id = request.auth["user_id"]
        
        # Ensure the sub_order belongs to the specified master_order owned by the user
        sub_order = get_object_or_404(SubOrder, id=sub_order_id, master_order__id=order_id, master_order__user_id=user_id)
        
        with transaction.atomic():
            master_order = sub_order.master_order
            
            # Reduce total amount
            # If rejected, it was already subtracted in BookingRejection logic
            if sub_order.status != "CANCELLED":
                 master_order.total_amount -= sub_order.amount
                 if master_order.total_amount < 0:
                     master_order.total_amount = 0
            
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
        
        # Self-healing: Sync total
        from django.db.models import Sum
        actual_total = order.sub_orders.exclude(status="CANCELLED").aggregate(Sum('amount'))['amount__sum'] or 0
        if order.total_amount != actual_total:
            order.total_amount = actual_total
            order.save(update_fields=['total_amount'])
            
        # Sync vendor names
        for sub in order.sub_orders.all():
            resolve_vendor_name(sub)
            
        return Response(MasterOrderSerializer(order).data)
