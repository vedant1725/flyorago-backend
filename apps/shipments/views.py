from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Shipment, ShipmentLog
from .serializers import ShipmentSerializer, ShipmentCreateSerializer, ShipmentUpdateStatusRequestSerializer
from bookings.models import Booking
from common.responses import success_response, failure_response


class ShipmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShipmentCreateSerializer
        return ShipmentSerializer

    def get_queryset(self):
        admin_all = self.request.query_params.get('admin_all', 'false').lower() == 'true'
        if admin_all and (self.request.user.role == 'admin' or self.request.user.is_staff):
            return Shipment.objects.all().select_related('booking__sender', 'booking__traveler', 'booking__trip').prefetch_related('logs')
        # Fetch shipments where active user is sender or traveler in booking
        return Shipment.objects.filter(
            Q(booking__sender=self.request.user) | Q(booking__traveler=self.request.user)
        ).select_related('booking__sender', 'booking__traveler', 'booking__trip').prefetch_related('logs')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Shipments list fetched")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.validated_data['booking']
            
            # Verify if user has access to booking
            is_admin = (request.user.role == 'admin' or request.user.is_staff)
            if booking.sender != request.user and booking.traveler != request.user and not is_admin:
                return failure_response(message="Access denied to booking reference", status_code=status.HTTP_403_FORBIDDEN)

            shipment = serializer.save()
            
            # Add initial progress log
            ShipmentLog.objects.create(
                shipment=shipment,
                status='Package Received',
                location=booking.trip.from_location if booking.trip else 'Origin',
                description="Cargo Package Checked-in. Processed at airport baggage terminal."
            )
            
            full_data = ShipmentSerializer(shipment).data
            return success_response(data=full_data, message="Shipment tracking initialized", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to initialize tracking")

class ShipmentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShipmentSerializer
    
    def get_queryset(self):
        if self.request.user.role == 'admin' or self.request.user.is_staff:
            return Shipment.objects.all().select_related('booking__sender', 'booking__traveler', 'booking__trip').prefetch_related('logs')
        return Shipment.objects.filter(
            Q(booking__sender=self.request.user) | Q(booking__traveler=self.request.user)
        ).select_related('booking__sender', 'booking__traveler', 'booking__trip').prefetch_related('logs')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Shipment details fetched")

class ShipmentUpdateStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShipmentUpdateStatusRequestSerializer

    @extend_schema(request=ShipmentUpdateStatusRequestSerializer, responses={200: ShipmentSerializer})
    @transaction.atomic
    def post(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        new_status = request.data.get('status')
        location = request.data.get('location')
        description = request.data.get('description', '')

        # Authorization: Only the traveler carrying the shipment or admin can update status
        is_admin = (request.user.role == 'admin' or request.user.is_staff)
        if shipment.booking.traveler != request.user and not is_admin:
            return failure_response(message="Only the traveler carrying the package or admin can update tracking logs", status_code=status.HTTP_403_FORBIDDEN)

        if not new_status or new_status not in [choice[0] for choice in Shipment.STATUS_CHOICES]:
            return failure_response(message="Invalid status choice")

        # Update shipment status
        shipment.status = new_status
        shipment.save()

        # Update associated booking status
        booking = shipment.booking
        if new_status == 'In Transit':
            booking.status = 'In Transit'
        elif new_status == 'Delivered':
            booking.status = 'Delivered'
        booking.save()

        # Create history log
        log = ShipmentLog.objects.create(
            shipment=shipment,
            status=new_status,
            location=location,
            description=description
        )

        return success_response(
            data=ShipmentSerializer(shipment).data,
            message=f"Shipment progress log created: {new_status}"
        )
