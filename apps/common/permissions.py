from rest_framework import permissions

class IsKYCApproved(permissions.BasePermission):
    """
    Permission check for KYC status:
    - Safe HTTP methods (GET, HEAD, OPTIONS) are allowed so users can browse dashboard, trips, etc.
    - Unsafe HTTP methods (POST, PUT, PATCH, DELETE) STRICTLY REQUIRE profile.kyc_status == 'APPROVED'.
    - Users with KYC status NOT_SUBMITTED, PENDING, UNDER_REVIEW, or REJECTED cannot create trips, bookings, shipments, or execute payments.
    - Admins and staff are exempt.
    """
    message = "KYC approval is strictly required to perform this action. Your identity verification is either pending, rejected, or not submitted."

    def has_permission(self, request, view):
        # Allow read/view access for safe methods (Dashboard, viewing trips, notifications, etc.)
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


class IsSystemAdmin(permissions.BasePermission):
    """
    Allows access only to authenticated users who are staff, superusers, or have the role 'admin'.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and
            user.is_authenticated and
            (user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'admin')
        )


