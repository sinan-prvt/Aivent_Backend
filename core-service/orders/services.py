from orders.models import MasterOrder

def update_master_order_status(master_order):
    if master_order.status == "PAID":
        return

    sub_orders = master_order.sub_orders.all()
    if not sub_orders.exists():
        return

    total_items = sub_orders.count()
    approved_count = 0
    waiting_count = 0
    
    for sub in sub_orders:
        # Check sub_order status as fallback, but primary is the linked booking status
        b_status = getattr(sub, 'booking').status if hasattr(sub, 'booking') else 'AWAITING_APPROVAL'
        
        if b_status in ['APPROVED', 'CONFIRMED']:
            approved_count += 1
        elif b_status == 'AWAITING_APPROVAL':
            waiting_count += 1
            
    if waiting_count > 0:
        master_order.status = "AWAITING_APPROVAL"
    elif approved_count == total_items:
        master_order.status = "FULLY_APPROVED"
    else:
        # Items are decided but not all approved (some rejected/cancelled)
        master_order.status = "PARTIALLY_APPROVED"
        
    master_order.save(update_fields=["status"])
