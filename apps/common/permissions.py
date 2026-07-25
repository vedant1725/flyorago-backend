from rest_framework import permissions

class IsKYCApproved(permissions.BasePermission):
    """
    Permission check for KYC status:
    - Safe HTTP methods (GET, HEAD, OPTIONS) are allowed so users can view their dashboard and lists.
    - Unsafe HTTP methods (POST, PUT, PATCH, DELETE) require user's KYC status to be 'APPROVED'.
    - Admins and staff users are always allowed.
    """
    message = "KYC approval is required to create requests or perform actions. Your KYC status is currently pending or not approved."

    def has_permission(self, request, view):
        # Allow read/view access for safe methods
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Admins and staff are exempt
        if getattr(user, 'role', '') == 'admin' or user.is_staff or user.is_superuser:
            return True

        # Check user profile KYC status
        profile = getattr(user, 'profile', None)
        if not profile:
            return False

        return profile.kyc_status == 'APPROVED'
