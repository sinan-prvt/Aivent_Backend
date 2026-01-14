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

class StatelessJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Returns a stateless user object based on the token.
        Does NOT check the database.
        """
        try:
            user_id = validated_token.get('user_id')
            return SimpleUser(user_id)
        except Exception:
            return None
