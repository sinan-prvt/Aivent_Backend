import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PaymentInitiateSerializer
from .models import Payment
import logging
from django.shortcuts import get_object_or_404
from razorpay.errors import SignatureVerificationError
import requests

logger = logging.getLogger(__name__)

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class PaymentInitiateAPIView(APIView):
    def post(self, request):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return Response(
                {"detail": "Razorpay keys are missing from environment. Check your .env file and docker-compose.yml"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data["order_id"]
        amount = serializer.validated_data["amount"]
        currency = serializer.validated_data["currency"]
        
        # 0. Check if payment already exists for this order
        existing_payment = Payment.objects.filter(order_id=order_id).first()
        if existing_payment:
            return Response({
                "platform_order_id": str(order_id),
                "razorpay_order_id": existing_payment.razorpay_order_id,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": str(existing_payment.amount),
                "currency": existing_payment.currency,
                "status": existing_payment.status,
                "note": "Existing payment returned"
            }, status=status.HTTP_200_OK)

        # Razorpay expects amount in paise
        amount_paise = int(amount * 100)
        
        try:
            # 1. Create Order in Razorpay
            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": currency,
                "payment_capture": 1 # Auto capture
            })
            
            # 2. Save Payment record in our DB
            payment = Payment.objects.create(
                order_id=order_id,
                razorpay_order_id=razorpay_order["id"],
                amount=amount,
                currency=currency,
                status="CREATED"
            )
            
            return Response({
                "platform_order_id": str(order_id),
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": str(amount),
                "currency": currency
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            error_detail = str(e) if settings.DEBUG else "Could not initiate payment"
            return Response(
                {"detail": error_detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentMockSuccessAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")

        if not razorpay_order_id:
            return Response(
                {"detail": "razorpay_order_id required"},
                status=400
            )

        payment = get_object_or_404(
            Payment,
            razorpay_order_id=razorpay_order_id,
            status="CREATED"
        )

        payment.status = "SUCCESS"
        payment.save(update_fields=["status"])

        # 🔔 Notify core-service (Mock version)
        try:
            requests.post(
                "http://core-service:8000/internal/payments/success/",
                json={"order_id": str(payment.order_id)},
                timeout=5,
            )
        except Exception as e:
            logger.error(f"Failed to notify core-service: {e}")

        return Response({
            "status": "PAYMENT_SUCCESS",
            "order_id": str(payment.order_id)
        })

class PaymentVerifyAPIView(APIView):
    def post(self, request):
        data = request.data
        required_keys = ["razorpay_order_id", "razorpay_payment_id", "razorpay_signature"]
        
        # Check for missing keys to avoid KeyError
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            return Response(
                {"detail": f"Missing keys: {', '.join(missing_keys)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": data["razorpay_order_id"],
                "razorpay_payment_id": data["razorpay_payment_id"],
                "razorpay_signature": data["razorpay_signature"],
            })
        except SignatureVerificationError:
            return Response(
                {"detail": "Invalid signature"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return Response(
                {"detail": f"Verification error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(
                razorpay_order_id=data["razorpay_order_id"]
            )
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment record not found for this razorpay_order_id"},
                status=status.HTTP_404_NOT_FOUND
            )

        payment.status = "PAID"
        payment.save(update_fields=["status"])

        # 🔔 Notify core-service
        try:
            requests.post(
                "http://core-service:8000/internal/payments/success/",
                json={"order_id": str(payment.order_id)},
                timeout=5,
            )
        except Exception as e:
            logger.error(f"Failed to notify core-service: {e}")
            return Response({
                "status": "PAYMENT_SUCCESS",
                "warning": "Payment verified but failed to notify core-service"
            })

        return Response({"status": "PAYMENT_SUCCESS"})