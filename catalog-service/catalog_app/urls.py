from django.urls import path
from catalog_app.views.public import (
    CategoryListView,
    ProductByCategoryView,
    ProductDetailView,
    ProductListView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view()),
    path("categories/<slug:slug>/products/", ProductByCategoryView.as_view()),
    path("products/", ProductListView.as_view()),
    path("products/<int:pk>/", ProductDetailView.as_view()),
]