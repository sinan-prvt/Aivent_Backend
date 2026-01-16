import pytest
from django.urls import reverse
from rest_framework import status
from .models.category import Category

@pytest.mark.django_db
class TestCategoryListView:
    def test_get_categories(self, api_client):
        # Create categories
        Category.objects.create(name="Electronics", slug="electronics")
        Category.objects.create(name="Fashion", slug="fashion")
        
        url = reverse("category-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2
        assert any(c["name"] == "Electronics" for c in response.data)
