import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

# Since auth is decoupled, we might need to mock user or use a test user model if it exists
User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="testvendor",
        email="vendor@example.com",
        password="testpassword123",
        role="vendor"
    )

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client
