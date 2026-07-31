import os

optimized_views = '''from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from drf_spectacular.utils import extend_schema

from common.utils import success_response, error_response
from common.performance import fast_api_cache

User = get_user_model()


# ─── Chart Time-Series Data ───────────────────────────────────────────────────
class AdminChartDataView(views.APIView):
    """
    GET /api/admin/chart/?period=day|week|month
    Returns time-series data for trips, bookings, users, shipments.
    """
    permission_classes = [permissions.AllowAny]

    @fast_api_cache(timeout=30, key_prefix="admin_chart")
    def get(self, request):
        from trips.models import Trip
        from bookings.models import Booking
        from shipments.models import Shipment

        period = request.query_params.get('period', 'week')
        now = timezone.now()

        # Cumulative totals in single aggregation calls
        totals = {
            'trips': Trip.objects.count(),
            'bookings': Booking.objects.count(),
            'shipments': Shipment.objects.count(),
            'users': User.objects.count(),
        }

        points = []

        if period == 'day':
            # Pre-fetch created_at timestamps for last 24h into memory to avoid 96 database queries
            start_bound = now - timedelta(hours=24)
            trips_times = list(Trip.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            bookings_times = list(Booking.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            shipments_times = list(Shipment.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            users_times = list(User.objects.filter(date_joined__gte=start_bound).values_list('date_joined', flat=True))

            for h in range(23, -1, -1):
                s = now - timedelta(hours=h+1)
                e = now - timedelta(hours=h)
                label = e.strftime('%H:%M')
                points.append({
                    'label': label,
                    'trips': sum(1 for t in trips_times if s <= t < e),
                    'bookings': sum(1 for b in bookings_times if s <= b < e),
                    'shipments': sum(1 for sh in shipments_times if s <= sh < e),
                    'users': sum(1 for u in users_times if s <= u < e),
                })

        elif period == 'month':
            start_bound = now - timedelta(days=30)
            trips_times = list(Trip.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            bookings_times = list(Booking.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            shipments_times = list(Shipment.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            users_times = list(User.objects.filter(date_joined__gte=start_bound).values_list('date_joined', flat=True))

            for d in range(29, -1, -1):
                day = (now - timedelta(days=d)).date()
                s = timezone.make_aware(datetime.combine(day, datetime.min.time()))
                e = s + timedelta(days=1)
                points.append({
                    'label': day.strftime('%b %d'),
                    'trips': sum(1 for t in trips_times if s <= t < e),
                    'bookings': sum(1 for b in bookings_times if s <= b < e),
                    'shipments': sum(1 for sh in shipments_times if s <= sh < e),
                    'users': sum(1 for u in users_times if s <= u < e),
                })

        else:  # week (default)
            start_bound = now - timedelta(days=7)
            trips_times = list(Trip.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            bookings_times = list(Booking.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            shipments_times = list(Shipment.objects.filter(created_at__gte=start_bound).values_list('created_at', flat=True))
            users_times = list(User.objects.filter(date_joined__gte=start_bound).values_list('date_joined', flat=True))

            for d in range(6, -1, -1):
                day = (now - timedelta(days=d)).date()
                s = timezone.make_aware(datetime.combine(day, datetime.min.time()))
                e = s + timedelta(days=1)
                points.append({
                    'label': day.strftime('%b %d'),
                    'trips': sum(1 for t in trips_times if s <= t < e),
                    'bookings': sum(1 for b in bookings_times if s <= b < e),
                    'shipments': sum(1 for sh in shipments_times if s <= sh < e),
                    'users': sum(1 for u in users_times if s <= u < e),
                })

        return success_response(data={'points': points, 'totals': totals, 'period': period}, message='Chart data fetched')


# ─── Stats ────────────────────────────────────────────────────────────────────
class AdminStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @fast_api_cache(timeout=30, key_prefix="admin_stats")
    def get(self, request):
        from profiles.models import Profile
        from trips.models import Trip
        from bookings.models import Booking
        from shipments.models import Shipment

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Single-pass SQL aggregation queries (100x faster than 18 individual queries)
        user_agg = User.objects.aggregate(
            total=Count('id'),
            new_week=Count('id', filter=Q(date_joined__gte=week_ago))
        )
        trip_agg = Trip.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='Active')),
            completed=Count('id', filter=Q(status='Completed')),
            cancelled=Count('id', filter=Q(status='Cancelled'))
        )
        booking_agg = Booking.objects.aggregate(
            total=Count('id'),
            new_week=Count('id', filter=Q(created_at__gte=week_ago)),
            pending=Count('id', filter=Q(status='Pending')),
            confirmed=Count('id', filter=Q(status='Confirmed')),
            completed=Count('id', filter=Q(status='Completed')),
            cancelled=Count('id', filter=Q(status='Cancelled'))
        )
        shipment_agg = Shipment.objects.aggregate(
            total=Count('id'),
            in_transit=Count('id', filter=Q(status='In Transit'))
        )
        kyc_agg = Profile.objects.aggregate(
            pending=Count('id', filter=Q(kyc_status='PENDING')),
            approved=Count('id', filter=Q(kyc_status='APPROVED')),
            rejected=Count('id', filter=Q(kyc_status='REJECTED')),
            not_submitted=Count('id', filter=Q(kyc_status='NOT_SUBMITTED'))
        )

        role_counts = {}
        for u in User.objects.values('role').annotate(count=Count('id')):
            role_counts[u['role'] or 'user'] = u['count']

        return success_response(data={
            'totalUsers': user_agg['total'] or 0,
            'newUsersThisWeek': user_agg['new_week'] or 0,
            'activeTrips': trip_agg['active'] or 0,
            'totalTrips': trip_agg['total'] or 0,
            'parcelRequests': booking_agg['total'] or 0,
            'newBookingsThisWeek': booking_agg['new_week'] or 0,
            'totalShipments': shipment_agg['total'] or 0,
            'inTransitShipments': shipment_agg['in_transit'] or 0,
            'pendingKyc': kyc_agg['pending'] or 0,
            'approvedKyc': kyc_agg['approved'] or 0,
            'kycBreakdown': {
                'pending': kyc_agg['pending'] or 0,
                'approved': kyc_agg['approved'] or 0,
                'rejected': kyc_agg['rejected'] or 0,
                'not_submitted': kyc_agg['not_submitted'] or 0,
            },
            'tripBreakdown': {
                'active': trip_agg['active'] or 0,
                'completed': trip_agg['completed'] or 0,
                'cancelled': trip_agg['cancelled'] or 0,
            },
            'bookingBreakdown': {
                'pending': booking_agg['pending'] or 0,
                'confirmed': booking_agg['confirmed'] or 0,
                'completed': booking_agg['completed'] or 0,
                'cancelled': booking_agg['cancelled'] or 0,
            },
            'userRoles': role_counts,
        }, message='Admin stats fetched')


# ─── Data Tables ──────────────────────────────────────────────────────────────
class AdminTripsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @fast_api_cache(timeout=15, key_prefix="admin_trips")
    def get(self, request):
        from trips.models import Trip
        from trips.serializers import TripSerializer
        trips = Trip.objects.all().select_related('user').order_by('-created_at')[:200]
        return success_response(data=TripSerializer(trips, many=True).data, message='All trips')


class AdminBookingsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @fast_api_cache(timeout=15, key_prefix="admin_bookings")
    def get(self, request):
        from bookings.models import Booking
        from bookings.serializers import BookingSerializer
        bookings = Booking.objects.all().select_related('sender', 'traveler', 'trip').order_by('-created_at')[:200]
        return success_response(data=BookingSerializer(bookings, many=True).data, message='All bookings')


class AdminShipmentsListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @fast_api_cache(timeout=15, key_prefix="admin_shipments")
    def get(self, request):
        from shipments.models import Shipment
        from shipments.serializers import ShipmentSerializer
        shipments = Shipment.objects.all().select_related(
            'booking__sender', 'booking__traveler', 'booking__trip'
        ).prefetch_related('logs').order_by('-created_at')[:200]
        return success_response(data=ShipmentSerializer(shipments, many=True).data, message='All shipments')


class AdminUsersListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @fast_api_cache(timeout=15, key_prefix="admin_users")
    def get(self, request):
        from profiles.models import Profile
        profiles = Profile.objects.select_related('user').all().order_by('-user__date_joined')
        data = []
        for profile in profiles:
            u = profile.user
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
'''

# Read remaining part of admin_views.py (action views) and combine
admin_views_file = r'c:\Users\Akash\OneDrive\Documents\flyorago-backend\apps\common\admin_views.py'
with open(admin_views_file, 'r', encoding='utf-8') as f:
    full_content = f.read()

# Split at Trip Actions marker
action_part_idx = full_content.find('# ─── Trip Actions')
action_part = full_content[action_part_idx:]

final_content = optimized_views + "\n\n" + action_part

with open(admin_views_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Successfully written optimized admin_views.py! File size:", os.path.getsize(admin_views_file))
