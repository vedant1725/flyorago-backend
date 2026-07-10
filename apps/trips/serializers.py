from rest_framework import serializers
from .models import Trip

class TripSerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    traveler_name = serializers.CharField(source='user.first_name', read_only=True)
    traveler_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Trip
        fields = (
            'id', 'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight', 'available_weight', 'status', 'created_at',
            'bookings_count', 'progress', 'traveler_name', 'traveler_email'
        )
        read_only_fields = ('id', 'created_at', 'available_weight')

    def get_bookings_count(self, obj) -> int:
        # We will retrieve booking count associated with this trip's route/user
        return obj.bookings.count() if hasattr(obj, 'bookings') else 0

    def get_progress(self, obj) -> int:
        if obj.capacity_weight <= 0:
            return 0
        used = obj.capacity_weight - obj.available_weight
        return int((used / obj.capacity_weight) * 100)

class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = (
            'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight'
        )

    def create(self, validated_data):
        # Default available weight to capacity weight initially
        validated_data['available_weight'] = validated_data.get('capacity_weight', 23.00)
        return super().create(validated_data)
