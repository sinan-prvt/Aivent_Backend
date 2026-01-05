from django.urls import path
from catalog_app.views.vendor import ( 
    VendorProductListCreateView,
    VendorProductDetailView,
)
from catalog_app.views.upload import UploadImageView

urlpatterns = [
    path("products/", VendorProductListCreateView.as_view()),
    path("products/<int:pk>/", VendorProductDetailView.as_view()),
    path("upload-image/", UploadImageView.as_view()),
]