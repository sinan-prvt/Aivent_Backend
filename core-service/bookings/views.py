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

        existing = IdempotencyKey.objects.filter(
            key=idem_key,
            user_id=request.auth["user_id"]
        ).first()

        if existing:
            return Response(existing.response, status=201)

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            booking = serializer.save(user_id=request.auth["user_id"])

            response_data = {"booking_id": str(booking.id)}

            IdempotencyKey.objects.create(
                key=idem_key,
                user_id=request.auth["user_id"],
                response=response_data
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

        return Response({"status": "CONFIRMED"})