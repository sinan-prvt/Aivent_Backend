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
                
                # 1. Create MasterOrder (one master per booking for now, can be expanded for cart)
                master_order = MasterOrder.objects.create(
                    user_id=user_id,
                    total_amount=amount,
                    status="PENDING"
                )
                
                # 2. Create SubOrder
                sub_order = SubOrder.objects.create(
                    master_order=master_order,
                    vendor_id=serializer.validated_data["vendor_id"],
                    amount=amount,
                    status="PENDING"
                )
                
                # 3. Create Booking linked to SubOrder
                booking = serializer.save(
                    user_id=user_id,
                    sub_order=sub_order
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