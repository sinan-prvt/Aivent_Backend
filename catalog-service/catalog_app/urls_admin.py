from django.urls import path
from catalog_app.views.admin import AdminApproveProductView

urlpatterns = [
    path("products/<int:pk>/review/", AdminApproveProductView.as_view()),
]