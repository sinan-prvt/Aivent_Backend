from django.db import transaction
from orders.models import MasterOrder

@transaction.atomic
def handle_payment_success(master_order_id):
    master = MasterOrder.objects.select_for_update().get(id=master_order_id)

    if master.status == "PAID":
        return

    master.status = "PAID"
    master.save(update_fields=["status"])

    for sub in master.sub_orders.all():
        sub.status = "PAID"
        sub.save(update_fields=["status"])

        if hasattr(sub, "booking"):
            sub.booking.confirm()
