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

    accepted_parcel_types = serializers.SerializerMethodField()

    def get_accepted_parcel_types(self, obj) -> list:
        raw = getattr(obj, 'accepted_parcel_types', None)
        if not raw:
            return []
        if isinstance(raw, list):
            return [
                t if (isinstance(t, str) and not t.startswith('data:image') and len(t) < 300) else '📦 Parcel Item'
                for t in raw
            ]
        if isinstance(raw, str) and not raw.startswith('data:image') and len(raw) < 300:
            return [raw]
        return ['📦 Parcel Item']

    def get_bookings_count(self, obj) -> int:
        if hasattr(obj, 'bookings_count_annotated'):
            return obj.bookings_count_annotated
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
            'capacity_weight', 'accepted_parcel_types'
        )

    def create(self, validated_data):
        # Default available weight to capacity weight initially
        validated_data['available_weight'] = validated_data.get('capacity_weight', 23.00)
        return super().create(validated_data)
