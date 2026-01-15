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
        
        # 0. Check if a successful payment already exists
        successful_payment = Payment.objects.filter(
            order_id=order_id, 
            status__in=["PAID", "COD_CONFIRMED"]
        ).first()
        
        if successful_payment:
            # Self-healing: Ensure core-service knows it's paid
            try:
                # Use setting or fallback
                core_url = getattr(settings, "CORE_SERVICE_URL", "http://core-service:8000")
                requests.post(
                    f"{core_url}/internal/payments/success/",
                    json={"order_id": str(order_id)},
                    timeout=5
                )
            except Exception as e:
                logger.error(f"Self-healing notification failed: {e}")

            return Response({
                "detail": "Payment already confirmed! Please refresh the page.",
                "platform_order_id": str(order_id),
                "status": successful_payment.status,
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. Check for an existing CREATED payment to reuse
        existing_payment = Payment.objects.filter(
            order_id=order_id, 
            status="CREATED",
            payment_method="ONLINE"
        ).first()
        
        if existing_payment and existing_payment.razorpay_order_id:
            return Response({
                "platform_order_id": str(order_id),
                "razorpay_order_id": existing_payment.razorpay_order_id,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": str(existing_payment.amount),
                "currency": existing_payment.currency,
                "status": existing_payment.status,
                "note": "Existing payment record reused"
            }, status=status.HTTP_200_OK)

        # VALIDATION: Check Core Service status
        try:
            # We assume core-service is accessible at 'http://core-service:8000' within internal network
            # Pass the user's token for authorization
            auth_header = request.headers.get("Authorization")
            response = requests.get(
                f"http://core-service:8000/api/orders/{order_id}/",
                headers={"Authorization": auth_header},
                timeout=5
            )
            
            if response.status_code != 200:
                 logger.error(f"Core service failed: {response.status_code} - {response.text}")
                 return Response({
                     "detail": f"Could not verify order with core-service. Status: {response.status_code}, Response: {response.text}"
                 }, status=400)
            
            order_data = response.json()
            order_status = order_data.get("status")
            
            if order_status not in ["PARTIALLY_APPROVED", "PENDING", "APPROVED", "FULLY_APPROVED"]:
                 return Response(
                     {"detail": f"Order cannot be paid in current status: {order_status}"},
                     status=400
                 )
                 
            # Use the TRUSTED amount from core-service
            # Note: order_data['total_amount'] might be string
            amount_str = order_data.get("total_amount")
            amount = float(amount_str) # Override client amount
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return Response({"detail": "Order validation failed"}, status=500)

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


class PaymentCODAPIView(APIView):
    """
    Handles Cash On Delivery (COD) payment selection.
    Immediately confirms the order in the core-service.
    """
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data["order_id"]
        amount = serializer.validated_data["amount"]
        currency = serializer.validated_data["currency"]

        # Check if already paid
        existing_paid = Payment.objects.filter(
            order_id=order_id, 
            status__in=["PAID", "COD_CONFIRMED"]
        ).exists()
        
        if existing_paid:
            # Self-healing for COD: Ensure core-service knows it's paid
            try:
                core_url = getattr(settings, "CORE_SERVICE_URL", "http://core-service:8000")
                requests.post(
                    f"{core_url}/internal/payments/success/",
                    json={"order_id": str(order_id)},
                    timeout=5
                )
            except Exception as e:
                logger.error(f"Self-healing COD notification failed: {e}")

            return Response({"detail": "Order already processed! Please refresh the page."}, status=400)

        # Create COD Payment record
        payment = Payment.objects.create(
            order_id=order_id,
            amount=amount,
            currency=currency,
            payment_method="COD",
            status="COD_CONFIRMED"
        )

        # Notify core-service
        try:
            core_service_url = getattr(settings, "CORE_SERVICE_URL", "http://core-service:8000")
            resp = requests.post(
                f"{core_service_url}/internal/payments/success/",
                json={"order_id": str(order_id)},
                timeout=5,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to notify core-service about COD: {e}")
            return Response(
                {"detail": f"COD Confirmed locally, but failed to update order service: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "status": "COD_CONFIRMED",
            "order_id": str(order_id),
            "payment_method": "COD"
        }, status=status.HTTP_201_CREATED)


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