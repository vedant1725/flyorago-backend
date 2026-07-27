from django.urls import path
from .views import TripListCreateView, TripDetailView

urlpatterns = [
    path('', TripListCreateView.as_view(), name='trip_list_create'),
    path('<int:pk>', TripDetailView.as_view(), name='trip_detail'),
]
