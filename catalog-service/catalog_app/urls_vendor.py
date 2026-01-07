from django.urls import path
from catalog_app.views.vendor import VendorProductListCreateView, VendorProductDetailView
from catalog_app.views.upload import UploadImageView
from catalog_app.views.delivery import VendorDeliveryListCreateView, VendorDeliveryDetailView

urlpatterns = [
    # Products
    path("products/", VendorProductListCreateView.as_view()),
    path("products/<int:pk>/", VendorProductDetailView.as_view()),
    path("upload-image/", UploadImageView.as_view()),

    # Deliveries
    path('deliveries/', VendorDeliveryListCreateView.as_view(), name='vendor-delivery-list'),
    path('deliveries/<int:pk>/', VendorDeliveryDetailView.as_view(), name='vendor-delivery-detail'),
]