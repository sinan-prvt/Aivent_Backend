from django.urls import path
from .views import PaymentInitiateAPIView, PaymentMockSuccessAPIView, PaymentVerifyAPIView

urlpatterns = [
    path("initiate/", PaymentInitiateAPIView.as_view(), name="initiate-payment"),
    path("mock-success/", PaymentMockSuccessAPIView.as_view()),
    path("verify/", PaymentVerifyAPIView.as_view()),
]
