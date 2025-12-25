from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user:
            return False

        return (
            getattr(user, "is_authenticated", False) is True
            and getattr(user, "role", None) == "admin"
        )