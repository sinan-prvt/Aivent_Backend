from django.urls import path
from catalog_app.views.admin import AdminApproveProductView, AdminProductListView

urlpatterns = [
    path("products/<int:pk>/review/", AdminApproveProductView.as_view()),
    path("products/", AdminProductListView.as_view()),
]