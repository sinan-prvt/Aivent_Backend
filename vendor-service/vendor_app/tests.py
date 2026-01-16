import pytest
from django.urls import reverse
from rest_framework import status
from .models import VendorProfile

@pytest.mark.django_db
class TestVendorMeView:
    def test_get_vendor_me_authenticated(self, authenticated_client, test_user):
        # Create a vendor profile for the test user
        VendorProfile.objects.create(
            user_id=test_user.id,
            email=test_user.email,
            business_name="Test Business",
            status="approved"
        )
        
        url = reverse("vendor-me")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["business_name"] == "Test Business"

    def test_get_vendor_me_unauthenticated(self, api_client):
        url = reverse("vendor-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_vendor_me_no_profile(self, authenticated_client):
        url = reverse("vendor-me")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
