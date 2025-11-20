from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS

class ReadOnlyOrCurrentUserOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(getattr(user, "is_staff", False) or getattr(obj, "pk", None) == getattr(user, "pk", None))