from orders.models import MasterOrder

def update_master_order_status(master_order):
    sub_orders = master_order.sub_orders.all()
    # Check if any linked booking is still AWAITING_APPROVAL
    pending = False
    for sub in sub_orders:
        if hasattr(sub, 'booking') and sub.booking.status == 'AWAITING_APPROVAL':
            pending = True
            break
            
    if not pending:
        # All decided
        master_order.status = "PARTIALLY_APPROVED"
        master_order.save(update_fields=["status"])
