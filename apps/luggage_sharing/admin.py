from django.contrib import admin
from .models import (
    LuggageListing, LuggageBooking, LuggageVerification,
    LuggageQRLog, LuggageOTPLog, LuggageTracking,
    LuggageReview, LuggageDispute
)

@admin.register(LuggageListing)
class LuggageListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'airline', 'flight_number', 'departure_airport', 'arrival_airport', 'departure_date', 'available_weight', 'price_per_kg', 'status')
    list_filter = ('status', 'cabin_class', 'airline', 'departure_date')
    search_fields = ('airline', 'flight_number', 'departure_airport', 'arrival_airport', 'owner__email')

@admin.register(LuggageBooking)
class LuggageBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'booker', 'owner', 'booked_weight', 'total_price', 'status', 'escrow_status', 'created_at')
    list_filter = ('status', 'escrow_status', 'created_at')
    search_fields = ('qr_code_token', 'otp_code', 'booker__email', 'owner__email')

@admin.register(LuggageVerification)
class LuggageVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'verified_by', 'weight', 'is_approved', 'timestamp')

@admin.register(LuggageQRLog)
class LuggageQRLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'scanned_by', 'qr_token', 'is_success', 'timestamp')

@admin.register(LuggageOTPLog)
class LuggageOTPLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'entered_by', 'otp_entered', 'is_success', 'timestamp')

@admin.register(LuggageTracking)
class LuggageTrackingAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'status', 'location_name', 'timestamp')

@admin.register(LuggageReview)
class LuggageReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'reviewer', 'reviewee', 'rating', 'created_at')

@admin.register(LuggageDispute)
class LuggageDisputeAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'raised_by', 'reason', 'status', 'created_at')
