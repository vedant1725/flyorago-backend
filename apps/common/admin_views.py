"""
Admin Dashboard API Views — AllowAny (protected by frontend localStorage auth)
"""
from rest_framework import views, permissions
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime, date

from common.responses import success_response, failure_response

User = get_user_model()


# ─── Chart Time-Series Data ───────────────────────────────────────────────────
class AdminChartDataView(views.APIView):
    """
    GET /api/admin/chart/?period=day|week|month
    Returns time-series data for trips, bookings, users, shipments.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from trips.models import Trip
        from bookings.models import Booking
        from shipments.models import Shipment

        period = request.query_params.get('period', 'week')
        now = timezone.now()

        if period == 'day':
            # Last 24 hours — group by hour
            labels, points = [], []
            for h in range(23, -1, -1):
                start = now - timedelta(hours=h+1)
                end   = now - timedelta(hours=h)
                label = (now - timedelta(hours=h)).strftime('%H:%M')
                points.append({
                    'label': label,
                    'trips': Trip.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'bookings': Booking.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'shipments': Shipment.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'users': User.objects.filter(date_joined__gte=start, date_joined__lt=end).count(),
                })

        elif period == 'month':
            # Last 30 days — group by day
            points = []
            for d in range(29, -1, -1):
                day = (now - timedelta(days=d)).date()
                start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
                end   = start + timedelta(days=1)
                points.append({
                    'label': day.strftime('%b %d'),
                    'trips': Trip.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'bookings': Booking.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'shipments': Shipment.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'users': User.objects.filter(date_joined__gte=start, date_joined__lt=end).count(),
                })

        else:  # week (default)
            points = []
            for d in range(6, -1, -1):
                day = (now - timedelta(days=d)).date()
                start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
                end   = start + timedelta(days=1)
                points.append({
                    'label': day.strftime('%b %d'),
                    'trips': Trip.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'bookings': Booking.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'shipments': Shipment.objects.filter(created_at__gte=start, created_at__lt=end).count(),
                    'users': User.objects.filter(date_joined__gte=start, date_joined__lt=end).count(),
                })

        # Cumulative totals for reference
        totals = {
            'trips': Trip.objects.count(),
            'bookings': Booking.objects.count(),
            'shipments': Shipment.objects.count(),
            'users': User.objects.count(),
        }

        return success_response(data={'points': points, 'totals': totals, 'period': period}, message='Chart data fetched')



# ─── Stats ────────────────────────────────────────────────────────────────────
class AdminStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from profiles.models import Profile
        from trips.models import Trip
        from bookings.models import Booking
        from shipments.models import Shipment

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        total_users = User.objects.count()
        new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
        active_trips = Trip.objects.filter(status__in=['Active', 'ACTIVE', 'Active Trip']).count()
        total_trips = Trip.objects.count()
        parcel_requests = Booking.objects.count()
        new_bookings_week = Booking.objects.filter(created_at__gte=week_ago).count()
        total_shipments = Shipment.objects.count()
        in_transit = Shipment.objects.filter(status__in=['In Transit', 'IN_TRANSIT', 'Out for Handoff']).count()
        pending_kyc = Profile.objects.filter(kyc_status='PENDING').count()
        approved_kyc = Profile.objects.filter(kyc_status='APPROVED').count()

        role_counts = {}
        for u in User.objects.values('role').annotate(count=Count('id')):
            role_counts[u['role'] or 'user'] = u['count']

        return success_response(data={
            'totalUsers': total_users,
            'newUsersThisWeek': new_users_week,
            'activeTrips': active_trips,
            'totalTrips': total_trips,
            'parcelRequests': parcel_requests,
            'newBookingsThisWeek': new_bookings_week,
            'totalShipments': total_shipments,
            'inTransitShipments': in_transit,
            'pendingKyc': pending_kyc,
            'approvedKyc': approved_kyc,
            'kycBreakdown': {
                'pending': pending_kyc,
                'approved': approved_kyc,
                'rejected': Profile.objects.filter(kyc_status='REJECTED').count(),
                'not_submitted': Profile.objects.filter(kyc_status='NOT_SUBMITTED').count(),
            },
            'tripBreakdown': {
                'active': active_trips,
                'completed': Trip.objects.filter(status__in=['Completed', 'COMPLETED', 'PAYMENT_RELEASED']).count(),
                'cancelled': Trip.objects.filter(status__in=['Cancelled', 'CANCELLED']).count(),
            },
            'bookingBreakdown': {
                'pending': Booking.objects.filter(status__in=['REQUEST_CREATED', 'REQUEST_SENT', 'Waiting Traveller', 'Draft', 'Pending', 'Booking Requested']).count(),
                'confirmed': Booking.objects.filter(status__in=['ACCEPTED', 'PAID', 'PARCEL_VERIFIED', 'Traveller Accepted', 'Confirmed', 'Payment Completed', 'Ready For Transit']).count(),
                'completed': Booking.objects.filter(status__in=['DELIVERED', 'PAYMENT_RELEASED', 'Completed']).count(),
                'cancelled': Booking.objects.filter(status__in=['REJECTED', 'CANCELLED', 'Cancelled', 'Rejected']).count(),
            },
            'userRoles': role_counts,
        }, message='Admin stats fetched')


# ─── Lists ────────────────────────────────────────────────────────────────────
class AdminTripsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from trips.models import Trip
        from trips.serializers import TripSerializer
        trips = Trip.objects.all().select_related('user').order_by('-created_at')[:200]
        return success_response(data=TripSerializer(trips, many=True).data, message='All trips')


class AdminBookingsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from bookings.models import Booking
        from bookings.serializers import BookingSerializer
        bookings = Booking.objects.all().select_related('sender', 'traveler', 'trip').order_by('-created_at')[:200]
        return success_response(data=BookingSerializer(bookings, many=True).data, message='All bookings')


class AdminShipmentsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from shipments.models import Shipment
        from shipments.serializers import ShipmentSerializer
        shipments = Shipment.objects.all().select_related(
            'booking__sender', 'booking__traveler', 'booking__trip'
        ).prefetch_related('logs').order_by('-created_at')[:200]
        return success_response(data=ShipmentSerializer(shipments, many=True).data, message='All shipments')


class AdminUsersListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from profiles.models import Profile
        users = User.objects.all().order_by('-date_joined')
        data = []
        for u in users:
            profile, _ = Profile.objects.get_or_create(user=u)
            data.append({
                'id': str(u.id),
                'email': u.email,
                'firstName': u.first_name,
                'lastName': u.last_name,
                'fullName': f"{u.first_name} {u.last_name}".strip() or u.email.split('@')[0],
                'phone': getattr(u, 'phone_number', '') or '',
                'role': u.role or 'user',
                'isActive': u.is_active,
                'isStaff': u.is_staff,
                'dateJoined': u.date_joined.isoformat() if u.date_joined else None,
                'kycStatus': profile.kyc_status,
            })
        return success_response(data=data, message='All users')


# ─── Trip Actions ─────────────────────────────────────────────────────────────
class AdminTripActionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        from trips.models import Trip
        from trips.serializers import TripSerializer
        try:
            trip = Trip.objects.get(pk=pk)
            new_status = request.data.get('status')
            if new_status:
                trip.status = new_status
                trip.save(update_fields=['status'])
            return success_response(data=TripSerializer(trip).data, message='Trip updated')
        except Trip.DoesNotExist:
            return failure_response(message='Trip not found', status_code=404)

    def delete(self, request, pk):
        from trips.models import Trip
        try:
            trip = Trip.objects.get(pk=pk)
            trip.delete()
            return success_response(message='Trip deleted successfully')
        except Trip.DoesNotExist:
            return failure_response(message='Trip not found', status_code=404)


# ─── Booking Actions ──────────────────────────────────────────────────────────
class AdminBookingActionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        from bookings.models import Booking
        from bookings.serializers import BookingSerializer
        try:
            booking = Booking.objects.get(pk=pk)
            new_status = request.data.get('status')
            if new_status:
                booking.status = new_status
                booking.save(update_fields=['status'])
            return success_response(data=BookingSerializer(booking).data, message='Booking updated')
        except Booking.DoesNotExist:
            return failure_response(message='Booking not found', status_code=404)

    def delete(self, request, pk):
        from bookings.models import Booking
        try:
            booking = Booking.objects.get(pk=pk)
            booking.delete()
            return success_response(message='Booking deleted')
        except Booking.DoesNotExist:
            return failure_response(message='Booking not found', status_code=404)


# ─── Shipment Actions ─────────────────────────────────────────────────────────
class AdminShipmentActionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        from shipments.models import Shipment
        from shipments.serializers import ShipmentSerializer
        try:
            shipment = Shipment.objects.get(pk=pk)
            new_status = request.data.get('status')
            if new_status:
                shipment.status = new_status
                shipment.save(update_fields=['status'])
            return success_response(data=ShipmentSerializer(shipment).data, message='Shipment updated')
        except Shipment.DoesNotExist:
            return failure_response(message='Shipment not found', status_code=404)

    def delete(self, request, pk):
        from shipments.models import Shipment
        try:
            shipment = Shipment.objects.get(pk=pk)
            shipment.delete()
            return success_response(message='Shipment deleted')
        except Shipment.DoesNotExist:
            return failure_response(message='Shipment not found', status_code=404)


# ─── User Actions ─────────────────────────────────────────────────────────────
class AdminUserActionView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            if 'is_active' in request.data:
                user.is_active = bool(request.data['is_active'])
            if 'role' in request.data:
                user.role = request.data['role']
            user.save()
            return success_response(message='User updated successfully')
        except User.DoesNotExist:
            return failure_response(message='User not found', status_code=404)

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            if user.is_staff or user.is_superuser:
                return failure_response(message='Cannot delete staff/superuser accounts', status_code=403)
            user.delete()
            return success_response(message='User deleted successfully')
        except User.DoesNotExist:
            return failure_response(message='User not found', status_code=404)
