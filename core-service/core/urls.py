from django.contrib import admin
from django.urls import path, include
from orders.views import PaymentSuccessAPIView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/bookings/", include("bookings.urls")),
    path("api/orders/", include("orders.urls")),

    path("internal/payments/success/", PaymentSuccessAPIView.as_view()),
]
