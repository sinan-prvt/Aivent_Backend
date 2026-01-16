import pytest
from django.urls import reverse
from rest_framework import status
from user_app.models import UserProfile

@pytest.mark.django_db
class TestProfileView:
    def test_get_profile_authenticated(self, authenticated_client, test_user):
        url = reverse("profile")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == test_user.username

    def test_get_profile_unauthenticated(self, api_client):
        url = reverse("profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_profile(self, authenticated_client):
        url = reverse("profile")
        data = {"full_name": "Updated Name", "city": "Test City"}
        response = authenticated_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Updated Name"
        assert response.data["city"] == "Test City"
