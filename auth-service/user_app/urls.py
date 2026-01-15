from django.urls import path
from .views import ProfileView, CustomerProfileRequestView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profiles/<int:user_id>/", CustomerProfileRequestView.as_view(), name="customer-profile-request"),
]
