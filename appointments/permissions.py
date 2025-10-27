from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsCustomerOrReadOnly(BasePermission):
    """
    Customers can create appointments (and manage their own).
    Providers can view and manage appointments for themselves (approve/reject/complete).
    Admins can do everything.
    """
    def has_permission(self, request, view):
        # allow list/detail for authenticated or anonymous read
        if request.method in SAFE_METHODS:
            return True
        # create allowed for authenticated customers
        if view.action == 'create':
            return request.user.is_authenticated and request.user.role == 'customer'
        # other mutating actions allowed for provider/admin (we do object checks later)
        return request.user.is_authenticated and request.user.role in ['provider', 'admin']

    def has_object_permission(self, request, view, obj):
        # read allowed to customer if they own, provider if their appointment, admin always
        if request.method in SAFE_METHODS:
            return (request.user.is_authenticated and
                    (request.user == obj.customer or request.user == obj.provider or request.user.role == 'admin'))

        # for mutations:
        # - customer may cancel/reschedule their own (object-level checks elsewhere for time-limits)
        # - provider may change status if they are provider
        # - admin can do all
        if request.user.role == 'admin':
            return True
        if request.user == obj.provider and request.user.role == 'provider':
            return True
        if request.user == obj.customer and request.user.role == 'customer':
            return True
        return False
