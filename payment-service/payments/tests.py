import pytest
import uuid
from payments.models import Payment

@pytest.mark.django_db
class TestPaymentModel:
    def test_create_payment(self):
        order_id = uuid.uuid4()
        payment = Payment.objects.create(
            order_id=order_id,
            amount=100.00,
            currency="INR"
        )
        assert payment.status == "CREATED"
        assert payment.payment_method == "ONLINE"

    def test_cod_payment(self):
        order_id = uuid.uuid4()
        payment = Payment.objects.create(
            order_id=order_id,
            amount=100.00,
            payment_method="COD",
            status="COD_CONFIRMED"
        )
        assert payment.status == "COD_CONFIRMED"
