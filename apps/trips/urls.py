from django.urls import path
from .views import TripListCreateView, TripDetailView
from .location_views import LocationSearchView

urlpatterns = [
    path('', TripListCreateView.as_view(), name='trip_list_create'),
    path('<int:pk>', TripDetailView.as_view(), name='trip_detail'),
    path('locations/search/', LocationSearchView.as_view(), name='trip_location_search'),
    path('locations/search', LocationSearchView.as_view(), name='trip_location_search_noslash'),
]
