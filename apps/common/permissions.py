from rest_framework import permissions

class IsKYCApproved(permissions.BasePermission):
    """
    Permission check for KYC status:
    - Safe HTTP methods (GET, HEAD, OPTIONS) are allowed.
    - Unsafe HTTP methods (POST, PUT, PATCH, DELETE) require active user access.
    - Explicitly REJECTED accounts are blocked from performing transactions.
    - Admins, staff, and verified/active members are allowed.
    """
    message = "Your KYC verification was rejected or restricted. Please contact support or re-submit valid ID documents."

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
            return True  # Allow active authenticated user if profile has not populated yet

        return profile.kyc_status != 'REJECTED'

