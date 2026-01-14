from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from core.authentication import StatelessJWTAuthentication
from core.permissions import HasValidJWT
from .serializers import BookingCreateSerializer
from bookings.tasks import publish_event_task
import uuid
from django.utils.timezone import now
from django.db import transaction, IntegrityError
from django.conf import settings
from bookings.models import IdempotencyKey
from bookings.models import Booking
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError


class BookingCreateAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def post(self, request):
        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return Response(
                {"detail": "Idempotency-Key header required"},
                status=400
            )

        user_id = request.auth["user_id"]
        existing = IdempotencyKey.objects.filter(
            key=idem_key,
            user_id=user_id
        ).first()

        if existing:
            return Response(existing.response, status=201)

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data.pop("amount")

        try:
            with transaction.atomic():
                from orders.models import MasterOrder, SubOrder
                
                # 1. Create or Get MasterOrder
                master_order_id = request.data.get("master_order_id")
                if master_order_id:
                    master_order = get_object_or_404(MasterOrder, id=master_order_id, user_id=user_id)
                    master_order.total_amount += amount
                    master_order.status = "AWAITING_APPROVAL" # Reset to waiting since we added a new pending item
                    master_order.save()
                else:
                    master_order = MasterOrder.objects.create(
                        user_id=user_id,
                        total_amount=amount,
                        status="AWAITING_APPROVAL"
                    )
                
                # 2. Create SubOrder
                sub_order = SubOrder.objects.create(
                    master_order=master_order,
                    vendor_id=serializer.validated_data["vendor_id"],
                    amount=amount,
                    status="PENDING"
                )
                
                # 3. Create Booking linked to SubOrder
                # We explicitly pass fields from validated_data to ensure they are persisted
                booking = serializer.save(
                    user_id=user_id,
                    sub_order=sub_order,
                    vendor_name=serializer.validated_data.get("vendor_name"),
                    product_name=serializer.validated_data.get("product_name"),
                    category_name=serializer.validated_data.get("category_name"),
                    event_type=serializer.validated_data.get("event_type"),
                    guests=serializer.validated_data.get("guests")
                )

                response_data = {
                    "booking_id": str(booking.id),
                    "master_order_id": str(master_order.id),
                    "sub_order_id": str(sub_order.id),
                    "total_amount": str(master_order.total_amount)
                }

                IdempotencyKey.objects.create(
                    key=idem_key,
                    user_id=user_id,
                    response=response_data
                )
        except IntegrityError:
            return Response(
                {"detail": "Vendor already booked for this date"},
                status=409
            )

        return Response(response_data, status=201)


class BookingConfirmAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def post(self, request, booking_id):
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user_id=request.auth["user_id"],
        )

        try:
            booking.confirm()
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"status": "CONFIRMED"}, status=status.HTTP_200_OK)


from orders.services import update_master_order_status

class VendorBookingApprovalAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def post(self, request, booking_id):
        vendor_id = request.auth["user_id"]
        booking = get_object_or_404(Booking, id=booking_id)
        
        if str(booking.vendor_id) != str(vendor_id):
            return Response({"detail": "This booking does not belong to you"}, status=403)
            
        if booking.status != "AWAITING_APPROVAL":
             return Response({"detail": "Booking is not awaiting approval"}, status=400)

        with transaction.atomic():
            booking.status = "APPROVED"
            booking.save(update_fields=["status"])
            
            # Check Master Order status
            update_master_order_status(booking.sub_order.master_order)

        return Response({"status": "APPROVED"})


class VendorBookingRejectionAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def post(self, request, booking_id):
        vendor_id = request.auth["user_id"]
        booking = get_object_or_404(Booking, id=booking_id)
        
        if str(booking.vendor_id) != str(vendor_id):
            return Response({"detail": "This booking does not belong to you"}, status=403)
            
        if booking.status != "AWAITING_APPROVAL":
             return Response({"detail": "Booking is not awaiting approval"}, status=400)

        with transaction.atomic():
            booking.status = "REJECTED"
            booking.save(update_fields=["status"])
            
            sub_order = booking.sub_order
            sub_order.status = "CANCELLED"
            sub_order.save(update_fields=["status"])
            
            # Reduce master order total
            master_order = sub_order.master_order
            master_order.total_amount -= sub_order.amount
            master_order.save(update_fields=["total_amount"])
            
            # Check Master Order status
            update_master_order_status(master_order)

        return Response({"status": "REJECTED"})