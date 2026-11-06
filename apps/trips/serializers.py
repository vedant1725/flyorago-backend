from rest_framework import serializers
from .models import Trip

class TripSerializer(serializers.ModelSerializer):
    bookings_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    traveler_name = serializers.SerializerMethodField()
    traveler_email = serializers.CharField(source='user.email', read_only=True)
    traveler_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Trip
        fields = (
            'id', 'user', 'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight', 'available_weight', 'price_per_kg', 'accepted_parcel_types', 'status', 'created_at',
            'bookings_count', 'progress', 'traveler_name', 'traveler_email', 'traveler_id'
        )
        read_only_fields = ('id', 'created_at', 'available_weight')

    def get_traveler_name(self, obj) -> str:
        if not obj.user:
            return "Traveler"
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return name or (obj.user.email.split('@')[0] if obj.user.email else "Traveler")

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
    flight_number = serializers.CharField(required=False, allow_blank=True, default='FL-101')
    airline = serializers.CharField(required=False, allow_blank=True, default='Domestic Travel')
    departure_time = serializers.CharField(required=False, allow_blank=True, default='10:00')
    arrival_date = serializers.DateField(required=False, allow_null=True)
    arrival_time = serializers.CharField(required=False, allow_blank=True, default='12:30')
    capacity_weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=20.00)
    available_weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=20.00)
    price_per_kg = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=15.00)
    status = serializers.CharField(required=False, default='Active')

    class Meta:
        model = Trip
        fields = (
            'flight_number', 'airline', 'aircraft',
            'from_location', 'to_location', 'from_airport', 'to_airport',
            'departure_date', 'departure_time', 'arrival_date', 'arrival_time',
            'duration', 'terminal_from', 'terminal_to', 'seats',
            'capacity_weight', 'available_weight', 'price_per_kg', 'accepted_parcel_types', 'status'
        )

    def validate(self, attrs):
        if not attrs.get('arrival_date') and attrs.get('departure_date'):
            attrs['arrival_date'] = attrs['departure_date']
        if not attrs.get('flight_number'):
            attrs['flight_number'] = 'FL-101'
        if not attrs.get('airline'):
            attrs['airline'] = 'Domestic Travel'
        if not attrs.get('departure_time'):
            attrs['departure_time'] = '10:00'
        if not attrs.get('arrival_time'):
            attrs['arrival_time'] = '12:30'
        if not attrs.get('status'):
            attrs['status'] = 'Active'
        return attrs

    def create(self, validated_data):
        if 'available_weight' not in validated_data or not validated_data['available_weight']:
            validated_data['available_weight'] = validated_data.get('capacity_weight', 20.00)
        return super().create(validated_data)
