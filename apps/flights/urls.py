from django.urls import path
from .views import FlightSearchView

urlpatterns = [
    path('search/', FlightSearchView.as_view(), name='flight-search'),
]
