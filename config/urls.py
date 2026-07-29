from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from profiles.views import KYCStatusView, KYCSubmitView, KYCAdminListView, KYCAdminActionView
<<<<<<< HEAD
from bookings.views import MatchTravellerListView, MatchShipmentListView
from config.views import api_root
from common.admin_views import (
    AdminStatsView, AdminChartDataView,
    AdminTripsListView, AdminBookingsListView, AdminShipmentsListView, AdminUsersListView,
    AdminTripActionView, AdminBookingActionView, AdminShipmentActionView, AdminUserActionView,
)

=======
from config.views import api_root
from bookings.views import MatchTravellerListView, MatchShipmentListView

from common.admin_views import (
    AdminShipmentsListView,
    AdminTripActionView, AdminBookingActionView, AdminShipmentActionView, AdminUserActionView,
)

from config.admin_views import (
    AdminUserListView, AdminTripListView, AdminBookingListView, 
    AdminTrustListView, AdminDisputeListView, AdminStatsView, AdminChartView
)

>>>>>>> b6aebf3ac52853fc37c85b070110a3846fe198e2
urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
<<<<<<< HEAD
    path('api/schema', SpectacularAPIView.as_view(), name='schema_noslash'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui_noslash'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc_noslash'),

    # ── Admin Panel: Stats & Lists & Chart ──
    path('api/admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('api/admin/stats', AdminStatsView.as_view(), name='admin_stats_noslash'),
    path('api/admin/chart/', AdminChartDataView.as_view(), name='admin_chart'),
    path('api/admin/chart', AdminChartDataView.as_view(), name='admin_chart_noslash'),
    path('api/admin/trips/', AdminTripsListView.as_view(), name='admin_trips'),
    path('api/admin/trips', AdminTripsListView.as_view(), name='admin_trips_noslash'),
    path('api/admin/bookings/', AdminBookingsListView.as_view(), name='admin_bookings'),
    path('api/admin/bookings', AdminBookingsListView.as_view(), name='admin_bookings_noslash'),
    path('api/admin/shipments/', AdminShipmentsListView.as_view(), name='admin_shipments'),
    path('api/admin/shipments', AdminShipmentsListView.as_view(), name='admin_shipments_noslash'),
    path('api/admin/users/', AdminUsersListView.as_view(), name='admin_users'),
    path('api/admin/users', AdminUsersListView.as_view(), name='admin_users_noslash'),

    # ── Admin Panel: CRUD Actions ──
    path('api/admin/trips/<int:pk>/', AdminTripActionView.as_view(), name='admin_trip_action'),
    path('api/admin/trips/<int:pk>', AdminTripActionView.as_view(), name='admin_trip_action_noslash'),
    path('api/admin/bookings/<int:pk>/', AdminBookingActionView.as_view(), name='admin_booking_action'),
    path('api/admin/bookings/<int:pk>', AdminBookingActionView.as_view(), name='admin_booking_action_noslash'),
    path('api/admin/shipments/<int:pk>/', AdminShipmentActionView.as_view(), name='admin_shipment_action'),
    path('api/admin/shipments/<int:pk>', AdminShipmentActionView.as_view(), name='admin_shipment_action_noslash'),
    path('api/admin/users/<str:pk>/', AdminUserActionView.as_view(), name='admin_user_action'),
    path('api/admin/users/<str:pk>', AdminUserActionView.as_view(), name='admin_user_action_noslash'),
=======
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ── Admin Panel: Stats & Lists & Chart ──
    path('api/admin/shipments/', AdminShipmentsListView.as_view(), name='admin_shipments'),

    # ── Admin Panel: CRUD Actions ──
    path('api/admin/trips/<int:pk>/', AdminTripActionView.as_view(), name='admin_trip_action'),
    path('api/admin/bookings/<int:pk>/', AdminBookingActionView.as_view(), name='admin_booking_action'),
    path('api/admin/shipments/<int:pk>/', AdminShipmentActionView.as_view(), name='admin_shipment_action'),
    path('api/admin/users/<str:pk>/', AdminUserActionView.as_view(), name='admin_user_action'),
>>>>>>> b6aebf3ac52853fc37c85b070110a3846fe198e2

    # Core API Modules
    path('api/auth/', include('users.urls_auth')),
    path('api/profiles/', include('profiles.urls')),

    # KYC
    path('api/kyc/status/<str:user_id>/', KYCStatusView.as_view(), name='kyc_status'),
<<<<<<< HEAD
    path('api/kyc/status/<str:user_id>', KYCStatusView.as_view(), name='kyc_status_noslash'),
    path('api/kyc/submit/', KYCSubmitView.as_view(), name='kyc_submit'),
    path('api/kyc/submit', KYCSubmitView.as_view(), name='kyc_submit_noslash'),
    path('api/kyc/admin/list/', KYCAdminListView.as_view(), name='kyc_admin_list'),
    path('api/kyc/admin/list', KYCAdminListView.as_view(), name='kyc_admin_list_noslash'),
    path('api/kyc/admin/action/', KYCAdminActionView.as_view(), name='kyc_admin_action'),
    path('api/kyc/admin/action', KYCAdminActionView.as_view(), name='kyc_admin_action_noslash'),
=======
    path('api/kyc/submit/', KYCSubmitView.as_view(), name='kyc_submit'),
    path('api/kyc/admin/list/', KYCAdminListView.as_view(), name='kyc_admin_list'),
    path('api/kyc/admin/action/', KYCAdminActionView.as_view(), name='kyc_admin_action'),

    # Restored Admin Panel Endpoints for Frontend
    path('api/admin/users/', AdminUserListView.as_view(), name='admin_users'),
    path('api/admin/trips/', AdminTripListView.as_view(), name='admin_trips'),
    path('api/admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('api/admin/bookings/', AdminBookingListView.as_view(), name='admin_bookings'),
    path('api/admin/chart/', AdminChartView.as_view(), name='admin_chart'),
    path('api/trust/admin/', AdminTrustListView.as_view(), name='admin_trust'),
    path('api/support/admin/disputes', AdminDisputeListView.as_view(), name='admin_disputes'),
    path('api/support/admin/disputes/', AdminDisputeListView.as_view(), name='admin_disputes_slash'),
>>>>>>> b6aebf3ac52853fc37c85b070110a3846fe198e2

    path('api/trips/', include('trips.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/shipments/', include('shipments.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/support/', include('support.urls')),
    path('api/flights/', include('flights.urls')),
    path('api/trust/', include('apps.trust_scores.urls')),
    path('api/luggage/', include('apps.luggage_sharing.urls')),

    # Matching Engine
    path('api/matches/find-travellers/<int:shipment_id>/', MatchTravellerListView.as_view(), name='match_travellers_root'),
    path('api/matches/find-shipments/<int:trip_id>/', MatchShipmentListView.as_view(), name='match_shipments_root'),
]
