from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

class StatelessJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        # DO NOT load user from DB
        return AnonymousUser()