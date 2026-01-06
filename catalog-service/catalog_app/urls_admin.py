from django.urls import path
from catalog_app.views.admin import AdminApproveProductView, AdminProductListView, AdminProductDetailView

urlpatterns = [
    path("products/<int:pk>/review/", AdminApproveProductView.as_view()),
    path("products/<int:pk>/", AdminProductDetailView.as_view()),
    path("products/", AdminProductListView.as_view()),
]