from rest_framework_simplejwt.authentication import JWTAuthentication

class SimpleUser:
    """
    A simple user class that mimics Django's User model
    but doesn't require database access.
    """
    def __init__(self, user_id):
        self.id = user_id
        self.pk = user_id
        self.username = f"user_{user_id}"
        self.email = ""
        self.is_authenticated = True
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False

    def __str__(self):
        return self.username

    @property
    def is_anonymous(self):
        return False

import jwt

class StatelessJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        """
        Validates the token and returns the validated token object.
        Overridden to add debug logging.
        """
        try:
            return super().get_validated_token(raw_token)
        except Exception as e:
            print(f"DEBUG: Token validation failed: {str(e)}")
            try:
                print(f"DEBUG: Token Header: {jwt.get_unverified_header(raw_token)}")
            except Exception as e2:
                print(f"DEBUG: Failed to decode header: {e2}")
            raise e

    def get_user(self, validated_token):
        """
        Returns a stateless user object based on the token.
        Does NOT check the database.
        """
        try:
            user_id = validated_token.get('user_id')
            if not user_id:
                 print("DEBUG: Token valid but missing user_id")
            return SimpleUser(user_id)
        except Exception as e:
            print(f"DEBUG: get_user failed: {e}")
            return None