from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.authentication import StatelessJWTAuthentication
from core.permissions import HasValidJWT
from .serializers import BookingCreateSerializer


class BookingCreateAPIView(APIView):
    authentication_classes = [StatelessJWTAuthentication]
    permission_classes = [HasValidJWT]

    def post(self, request):
        user_id = request.auth["user_id"]  # from JWT payload

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = serializer.save(user_id=user_id)

        return Response(
            {
                "booking_id": booking.id,
                "status": booking.status,
                "expires_at": booking.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )
