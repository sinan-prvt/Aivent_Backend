from django.urls import path
from catalog_app.views.vendor import ( 
    VendorProductListCreateView,
    VendorProductDetailView,
)

urlpatterns = [
    path("products/", VendorProductListCreateView.as_view()),
    path("products/<int:pk>/", VendorProductDetailView.as_view()),
]