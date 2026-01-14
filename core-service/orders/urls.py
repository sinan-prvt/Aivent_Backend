from django.urls import path
from orders.views import (
    PaymentSuccessAPIView,
    UserOrderListAPIView,
    VendorOrderListAPIView,
    AdminOrderListAPIView,
    AdminOrderUpdateAPIView,
    OrderDetailAPIView,
    SubOrderDeleteAPIView
)

urlpatterns = [
    # Existing internal callback
    path('internal/payments/success/', PaymentSuccessAPIView.as_view(), name='payment-success-internal'),
    
    # User API
    path('my-orders/', UserOrderListAPIView.as_view(), name='user-order-list'),
    path('<uuid:order_id>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('<uuid:order_id>/items/<uuid:sub_order_id>/', SubOrderDeleteAPIView.as_view(), name='order-item-delete'),
    
    # Vendor API
    path('vendor-orders/', VendorOrderListAPIView.as_view(), name='vendor-order-list'),
    
    # Admin API
    path('admin/orders/', AdminOrderListAPIView.as_view(), name='admin-order-list'),
    path('admin/orders/<uuid:order_id>/', AdminOrderUpdateAPIView.as_view(), name='admin-order-update'),
]
