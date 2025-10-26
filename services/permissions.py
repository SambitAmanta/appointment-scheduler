from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrProvider(BasePermission):
    """
    Admins and service providers can create/update/delete.
    Customers can only read.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['admin', 'provider']

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.provider == request.user or request.user.role == 'admin'
