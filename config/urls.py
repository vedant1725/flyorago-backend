from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from profiles.views import KYCStatusView, KYCSubmitView, KYCAdminListView, KYCAdminActionView
from bookings.views import MatchTravellerListView, MatchShipmentListView
from config.views import api_root

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    
    # API Schema and Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Core API Application Modules
    path('api/auth/', include('users.urls_auth')),
    path('api/profiles/', include('profiles.urls')),
    
    # KYC Specific Endpoints (Matching frontend calls)
    path('api/kyc/status/<str:user_id>/', KYCStatusView.as_view(), name='kyc_status'),
    path('api/kyc/submit/', KYCSubmitView.as_view(), name='kyc_submit'),
    path('api/kyc/admin/list/', KYCAdminListView.as_view(), name='kyc_admin_list'),
    path('api/kyc/admin/action/', KYCAdminActionView.as_view(), name='kyc_admin_action'),

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
    
    # Matching Engine
    path('api/matches/find-travellers/<int:shipment_id>/', MatchTravellerListView.as_view(), name='match_travellers_root'),
    path('api/matches/find-shipments/<int:trip_id>/', MatchShipmentListView.as_view(), name='match_shipments_root'),
]
