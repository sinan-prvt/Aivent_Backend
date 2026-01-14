from django.urls import path
from .views import PaymentInitiateAPIView, PaymentMockSuccessAPIView, PaymentVerifyAPIView, PaymentCODAPIView

urlpatterns = [
    path('initiate/', PaymentInitiateAPIView.as_view(), name='payment-initiate'),
    path('verify/', PaymentVerifyAPIView.as_view(), name='payment-verify'),
    path('cod/', PaymentCODAPIView.as_view(), name='payment-cod'),
    path('mock-success/', PaymentMockSuccessAPIView.as_view(), name='payment-mock-success'),
]
