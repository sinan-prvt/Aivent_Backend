from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser


class StatelessJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Override DB user lookup.
        Build a lightweight user object from token claims.
        """

        class JWTUser:
            is_authenticated = True

            def __init__(self, payload):
                self.id = payload.get("user_id")
                self.role = payload.get("role")
                self.email = payload.get("email")

            def __str__(self):
                return f"JWTUser(id={self.id}, role={self.role})"

        return JWTUser(validated_token)