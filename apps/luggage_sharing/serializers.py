from rest_framework import serializers
from users.serializers import UserSerializer
from .models import (
    LuggageListing, LuggageBooking, LuggageVerificationLog,
    LuggageWeightLog, LuggageRating, LuggageDispute
)

class LuggageListingSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)

    class Meta:
        model = LuggageListing
        fields = [
            'id', 'owner', 'owner_details', 'airline', 'flight_number',
            'departure_airport', 'arrival_airport', 'departure_date', 'departure_time',
            'cabin_class', 'max_airline_allowance', 'currently_used_weight',
            'available_weight', 'price_per_kg', 'min_kg', 'max_kg',
            'accept_partial_booking', 'instant_booking', 'insurance',
            'description', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'available_weight', 'created_at', 'updated_at']

    def validate(self, data):
        max_allowance = data.get('max_airline_allowance', 0)
        currently_used = data.get('currently_used_weight', 0)
        if currently_used > max_allowance:
            raise serializers.ValidationError("Currently used weight cannot exceed maximum airline allowance.")
        
        min_kg = data.get('min_kg', 1)
        max_kg = data.get('max_kg', 1)
        if min_kg > max_kg:
            raise serializers.ValidationError("Minimum KG cannot be greater than Maximum KG.")
        
        return data


class LuggageVerificationLogSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)

    class Meta:
        model = LuggageVerificationLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class LuggageWeightLogSerializer(serializers.ModelSerializer):
    logged_by_name = serializers.CharField(source='logged_by.get_full_name', read_only=True)

    class Meta:
        model = LuggageWeightLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class LuggageRatingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)

    class Meta:
        model = LuggageRating
        fields = '__all__'
        read_only_fields = ['id', 'reviewer', 'created_at']


class LuggageDisputeSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.CharField(source='raised_by.get_full_name', read_only=True)

    class Meta:
        model = LuggageDispute
        fields = '__all__'
        read_only_fields = ['id', 'raised_by', 'created_at', 'updated_at']


class LuggageBookingSerializer(serializers.ModelSerializer):
    listing_details = LuggageListingSerializer(source='listing', read_only=True)
    booker_details = UserSerializer(source='booker', read_only=True)
    owner_details = UserSerializer(source='owner', read_only=True)
    verification_logs = LuggageVerificationLogSerializer(many=True, read_only=True)
    weight_logs = LuggageWeightLogSerializer(many=True, read_only=True)
    ratings = LuggageRatingSerializer(many=True, read_only=True)
    disputes = LuggageDisputeSerializer(many=True, read_only=True)

    class Meta:
        model = LuggageBooking
        fields = [
            'id', 'listing', 'listing_details', 'booker', 'booker_details',
            'owner', 'owner_details', 'booked_weight', 'price_per_kg',
            'total_price', 'insurance_fee', 'status', 'escrow_status',
            'qr_code_token', 'meeting_time', 'meeting_point', 'terminal',
            'gate', 'notes', 'verification_logs', 'weight_logs',
            'ratings', 'disputes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'booker', 'owner', 'price_per_kg', 'total_price',
            'status', 'escrow_status', 'qr_code_token', 'created_at', 'updated_at'
        ]
