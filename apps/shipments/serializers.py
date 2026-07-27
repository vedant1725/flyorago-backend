from rest_framework import serializers
from .models import Shipment, ShipmentLog

class ShipmentLogSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ShipmentLog
        fields = ('id', 'status', 'location', 'description', 'timestamp')

    def get_timestamp(self, obj) -> str:
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')

class ShipmentSerializer(serializers.ModelSerializer):
    trackingNumber = serializers.CharField(source='tracking_number', read_only=True)
    packageName = serializers.CharField(source='booking.package_name', read_only=True)
    packageImage = serializers.CharField(source='booking.package_image', read_only=True)
    category = serializers.CharField(source='booking.package_category', read_only=True)
    weight = serializers.DecimalField(source='booking.weight', max_digits=5, decimal_places=2, read_only=True)
    senderName = serializers.SerializerMethodField()
    travelerName = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    flightNumber = serializers.CharField(source='booking.trip.flight_number', default='N/A', read_only=True)
    escrow = serializers.CharField(source='booking.escrow_status', default='Hold', read_only=True)
    pickupAddress = serializers.CharField(source='pickup_address')
    deliveryAddress = serializers.CharField(source='delivery_address')
    pickupDate = serializers.SerializerMethodField()
    
    logs = ShipmentLogSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'id', 'trackingNumber', 'status', 'pickupAddress', 'deliveryAddress',
            'dimensions', 'insurance', 'eta', 'created_at', 'updated_at',
            'packageName', 'packageImage', 'category', 'weight',
            'senderName', 'travelerName', 'origin', 'destination', 'flightNumber', 'escrow',
            'pickupDate', 'logs'
        )
        read_only_fields = ('id', 'trackingNumber', 'created_at', 'updated_at')

    def get_senderName(self, obj) -> str:
        return f"{obj.booking.sender.first_name} {obj.booking.sender.last_name}".strip() or obj.booking.sender.email.split('@')[0]

    def get_travelerName(self, obj) -> str:
        return f"{obj.booking.traveler.first_name} {obj.booking.traveler.last_name}".strip() or obj.booking.traveler.email.split('@')[0]

    def get_origin(self, obj) -> str:
        return obj.booking.trip.from_location if obj.booking.trip else 'Unknown'

    def get_destination(self, obj) -> str:
        return obj.booking.trip.to_location if obj.booking.trip else 'Unknown'

    def get_pickupDate(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d')

class ShipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ('booking', 'pickup_address', 'delivery_address', 'dimensions', 'insurance', 'eta')

class ShipmentUpdateStatusRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[choice[0] for choice in Shipment.STATUS_CHOICES], required=True)
    location = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

