from rest_framework.permissions import BasePermission

class HasValidJWT(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth)  # token decoded successfully
