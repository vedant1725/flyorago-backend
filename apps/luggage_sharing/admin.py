from django.contrib import admin
from .models import (
    LuggageListing, LuggageBooking, LuggageVerificationLog,
    LuggageWeightLog, LuggageRating, LuggageDispute
)

@admin.register(LuggageListing)
class LuggageListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'airline', 'flight_number', 'departure_airport', 'arrival_airport', 'available_weight', 'price_per_kg', 'status')
    list_filter = ('status', 'airline', 'cabin_class')
    search_fields = ('airline', 'flight_number', 'owner__email')

@admin.register(LuggageBooking)
class LuggageBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'booker', 'owner', 'booked_weight', 'total_price', 'status', 'escrow_status')
    list_filter = ('status', 'escrow_status')
    search_fields = ('qr_code_token', 'booker__email', 'owner__email')

@admin.register(LuggageVerificationLog)
class LuggageVerificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'verified_by', 'verification_type', 'is_success', 'timestamp')

@admin.register(LuggageWeightLog)
class LuggageWeightLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'stage', 'weight', 'timestamp')

@admin.register(LuggageRating)
class LuggageRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'reviewer', 'reviewee', 'overall_rating')

@admin.register(LuggageDispute)
class LuggageDisputeAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'raised_by', 'reason', 'status')
    list_filter = ('status',)
