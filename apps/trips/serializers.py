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
        if not getattr(obj, 'capacity_weight', None) or obj.capacity_weight <= 0:
            return 0
        avail = obj.available_weight if getattr(obj, 'available_weight', None) is not None else obj.capacity_weight
        used = obj.capacity_weight - avail
        return int((used / obj.capacity_weight) * 100)

class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = (
            'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight', 'available_weight', 'price_per_kg', 'status',
            'notes', 'transport_type', 'accepted_parcel_types'
        )

    def to_internal_value(self, data):
        # Normalize date strings if in MM/DD/YYYY format
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)
        for date_field in ['departure_date', 'arrival_date']:
            val = data_copy.get(date_field)
            if val and isinstance(val, str) and '/' in val:
                parts = val.split('/')
                if len(parts) == 3 and len(parts[2]) == 4:
                    try:
                        data_copy[date_field] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    except Exception:
                        pass
        return super().to_internal_value(data_copy)

    def create(self, validated_data):
        # Default available weight to capacity weight initially if not provided
        if not validated_data.get('available_weight'):
            validated_data['available_weight'] = validated_data.get('capacity_weight', 23.00)
        return super().create(validated_data)
