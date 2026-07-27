from django.urls import path
from .views import (
    LuggageDashboardView,
    LuggageListingListCreateView,
    LuggageListingDetailView,
    LuggageSearchMatchingView,
    LuggageBookingListCreateView,
    LuggageBookingActionView,
    LuggageQRVerificationView,
    LuggageWeightLogView,
    LuggageRatingView,
    LuggageDisputeView,
    LuggageAdminView
)

urlpatterns = [
    path('dashboard/', LuggageDashboardView.as_view(), name='luggage_dashboard'),
    path('listings/', LuggageListingListCreateView.as_view(), name='luggage_listings'),
    path('listings/<int:pk>/', LuggageListingDetailView.as_view(), name='luggage_listing_detail'),
    path('listings/search/', LuggageSearchMatchingView.as_view(), name='luggage_search'),
    path('bookings/', LuggageBookingListCreateView.as_view(), name='luggage_bookings'),
    path('bookings/<int:pk>/action/', LuggageBookingActionView.as_view(), name='luggage_booking_action'),
    path('bookings/<int:pk>/verify-qr/', LuggageQRVerificationView.as_view(), name='luggage_booking_verify_qr'),
    path('verify-qr/', LuggageQRVerificationView.as_view(), name='luggage_verify_qr_direct'),
    path('bookings/<int:pk>/weight-log/', LuggageWeightLogView.as_view(), name='luggage_booking_weight_log'),
    path('ratings/', LuggageRatingView.as_view(), name='luggage_ratings'),
    path('disputes/', LuggageDisputeView.as_view(), name='luggage_disputes'),
    path('admin/', LuggageAdminView.as_view(), name='luggage_admin'),
]
