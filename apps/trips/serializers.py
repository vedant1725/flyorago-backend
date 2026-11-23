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
            'id', 'user', 'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight', 'available_weight', 'accepted_parcel_types', 'status', 'created_at',
            'bookings_count', 'progress', 'traveler_name', 'traveler_email'
        )
        read_only_fields = ('id', 'created_at', 'available_weight')

    def get_bookings_count(self, obj) -> int:
        if not hasattr(obj, 'bookings'):
            return 0
        # Exclude rejected and cancelled bookings
        return obj.bookings.exclude(status__in=['REJECTED', 'CANCELLED']).count()

    def get_progress(self, obj) -> int:
        if obj.capacity_weight <= 0:
            return 0
        used = obj.capacity_weight - obj.available_weight
        return int((used / obj.capacity_weight) * 100)

class TripCreateSerializer(serializers.ModelSerializer):
    arrival_date = serializers.DateField(required=False, allow_null=True)
    arrival_time = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Trip
        fields = (
            'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight', 'accepted_parcel_types'
        )

    def create(self, validated_data):
        # Auto-fill arrival date and time if omitted by mobile or web form
        if not validated_data.get('arrival_date'):
            validated_data['arrival_date'] = validated_data.get('departure_date')
        if not validated_data.get('arrival_time'):
            validated_data['arrival_time'] = validated_data.get('departure_time') or '12:30:00'

        # Default available weight to capacity weight initially
        validated_data['available_weight'] = validated_data.get('capacity_weight', 23.00)
        return super().create(validated_data)
