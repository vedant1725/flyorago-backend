from django.urls import path
from .views import (
    BookingListCreateView, BookingDetailView, BookingActionView,
    MatchTravellerListView, MatchShipmentListView
)

urlpatterns = [
    path('', BookingListCreateView.as_view(), name='booking_list_create'),
    path('<int:pk>', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/action', BookingActionView.as_view(), name='booking_action'),
    
    # Matching Engine Endpoints
    path('matches/find-travellers/<int:shipment_id>/', MatchTravellerListView.as_view(), name='match_travellers'),
    path('matches/find-shipments/<int:trip_id>/', MatchShipmentListView.as_view(), name='match_shipments'),
]
