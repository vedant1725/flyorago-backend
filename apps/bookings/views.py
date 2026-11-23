from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer, BookingActionRequestSerializer
from trips.models import Trip
from trips.serializers import TripSerializer
from shipments.models import Shipment
from shipments.serializers import ShipmentSerializer
from common.responses import success_response, failure_response
from common.permissions import IsKYCApproved
from .services import MatchingService


class BookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        # Retrieve bookings where active user is sender OR traveler
        queryset = Booking.objects.all().select_related('sender', 'traveler', 'trip')
        
        user_only = self.request.query_params.get('user_only', 'true').lower() == 'true'
        admin_all = self.request.query_params.get('admin_all', 'false').lower() == 'true'
        
        if admin_all and (self.request.user.role == 'admin' or self.request.user.is_staff):
            pass  # Admins can view all bookings in the system
        elif user_only:
            queryset = queryset.filter(Q(sender=self.request.user) | Q(traveler=self.request.user))
            
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Bookings list fetched")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.validated_data['trip']
            weight = serializer.validated_data['weight']
            sender_trip = serializer.validated_data.get('sender_trip')
            
            # Reduce trip weight
            trip.available_weight -= weight
            trip.save()

            # Extract receiver details from sender_trip if not explicitly provided
            extra_kwargs = {}
            if sender_trip:
                if not serializer.validated_data.get('receiver_name') and sender_trip.terminal_from and sender_trip.terminal_from != 'N/A':
                    extra_kwargs['receiver_name'] = sender_trip.terminal_from
                if not serializer.validated_data.get('receiver_phone') and sender_trip.terminal_to and sender_trip.terminal_to != 'N/A':
                    extra_kwargs['receiver_phone'] = sender_trip.terminal_to
                if not serializer.validated_data.get('receiver_address') and sender_trip.to_location:
                    extra_kwargs['receiver_address'] = sender_trip.to_location

            booking = serializer.save(
                sender=request.user,
                traveler=trip.user,
                status='REQUEST_SENT',
                **extra_kwargs
            )
            
            full_data = BookingSerializer(booking).data
            return success_response(data=full_data, message="Booking request sent successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to create booking request")

class BookingDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer
    queryset = Booking.objects.all().select_related('sender', 'traveler', 'trip')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Booking details retrieved")

class BookingActionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]
    serializer_class = BookingActionRequestSerializer

    @extend_schema(request=BookingActionRequestSerializer, responses={200: BookingSerializer})
    @transaction.atomic
    def post(self, request, pk):
        from .services import BookingWorkflowService
        booking = get_object_or_404(Booking, pk=pk)
        action = request.data.get('action')

        if not action:
            return failure_response(message="Action is required")

        is_sender = (booking.sender == request.user)
        is_traveler = (booking.traveler == request.user)
        is_admin = (request.user.role == 'admin' or request.user.is_staff)

        if not is_sender and not is_traveler and not is_admin:
            return failure_response(message="Unauthorized action", status_code=status.HTTP_403_FORBIDDEN)

        try:
            if action == 'SEND_REQUEST':
                if not is_sender and not is_admin:
                    return failure_response(message="Only sender can send request")
                booking = BookingWorkflowService.send_request(booking)
                return success_response(data=BookingSerializer(booking).data, message="Booking request sent")

            elif action in ['ACCEPT', 'Accept']:
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can accept")
                booking = BookingWorkflowService.accept_request(booking)
                from notifications.models import Notification
                Notification.objects.create(
                    user=booking.sender,
                    title='Parcel Request Accepted 🎉',
                    message=f'Traveler accepted your request for parcel "{booking.package_name}". Proceed to payment!',
                    type='booking'
                )
                return success_response(data=BookingSerializer(booking).data, message="Booking accepted")

            elif action in ['REJECT', 'Reject']:
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can reject")
                booking.status = 'REJECTED'
                booking.save()
                if booking.trip and booking.weight:
                    booking.trip.available_weight += booking.weight
                    booking.trip.save()
                from notifications.models import Notification
                Notification.objects.create(
                    user=booking.sender,
                    title='Parcel Request Rejected ❌',
                    message=f'Traveler declined your request for parcel "{booking.package_name}".',
                    type='booking'
                )
                BookingWorkflowService.trigger_websocket_notification(
                    booking, 'rejected', f"Traveler rejected Booking #{booking.id}."
                )
                return success_response(data=BookingSerializer(booking).data, message="Booking rejected")

            elif action in ['PAY', 'MARK_PAYMENT_COMPLETED', 'DEPOSIT_ESCROW']:
                if not is_sender and not is_admin:
                    return failure_response(message="Only sender can pay")
                booking = BookingWorkflowService.process_payment(booking)
                return success_response(data=BookingSerializer(booking).data, message="Payment secured in Escrow")

            elif action == 'VERIFY_PARCEL':
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can verify parcel")
                # Save verification images if provided
                payload = request.data.get('payload', {})
                images = payload.get('images', []) if isinstance(payload, dict) else request.data.get('images', [])
                if images and isinstance(images, list):
                    import json
                    booking.package_image = json.dumps(images[:5])
                    booking.save(update_fields=['package_image'])
                booking = BookingWorkflowService.upload_verification(booking)
                return success_response(data=BookingSerializer(booking).data, message="Parcel verified")

            elif action == 'START_TRANSIT':
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can start transit")
                booking = BookingWorkflowService.update_transit_status(booking, 'IN_TRANSIT')
                return success_response(data=BookingSerializer(booking).data, message="Transit started")

            elif action in ['ARRIVED', 'FLIGHT_LANDED']:
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can mark arrived")
                booking = BookingWorkflowService.update_transit_status(booking, 'ARRIVED')
                return success_response(data=BookingSerializer(booking).data, message="Flight arrived")

            elif action == 'OUT_FOR_DELIVERY':
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can mark out for delivery")
                
                # Generate OTP
                calc_otp = str((booking.id * 3791 + 100000) % 900000 + 100000)
                booking.delivery_otp = calc_otp
                
                booking = BookingWorkflowService.update_transit_status(booking, 'OUT_FOR_DELIVERY')
                
                BookingWorkflowService.trigger_websocket_notification(
                    booking, 'otp_generated', f"OTP for Booking #{booking.id} has been generated."
                )
                return success_response(data=BookingSerializer(booking).data, message="Out for delivery. OTP Generated")

            elif action == 'CONFIRM_DELIVERY':
                raw_input = str(request.data.get('otp') or request.data.get('delivery_otp') or '').strip()
                # Support QR format prefix FLYORA-OTP-XXXXXX
                if 'FLYORA-OTP-' in raw_input.upper():
                    raw_input = raw_input.upper().replace('FLYORA-OTP-', '').strip()
                booking = BookingWorkflowService.complete_delivery(booking, raw_input)
                
                # Check if all bookings for this trip are completed/delivered; if so, mark Trip as Completed!
                if booking.trip:
                    trip = booking.trip
                    other_active = trip.bookings.exclude(status__in=['DELIVERED', 'PAYMENT_RELEASED', 'COMPLETED', 'CANCELLED', 'REJECTED']).exists()
                    if not other_active:
                        trip.status = 'Completed'
                        trip.save(update_fields=['status'])

                # Record completed trip statistics
                try:
                    profile = booking.traveler.profile
                    profile.completed_trips += 1
                    profile.trust_score += 5
                    profile.save()
                except Exception:
                    pass
                    
                return success_response(data=BookingSerializer(booking).data, message="Delivery confirmed")

            elif action == 'RELEASE_ESCROW':
                if not is_admin:
                    return failure_response(message="Only admin can release escrow manually")
                booking = BookingWorkflowService.release_escrow(booking)
                return success_response(data=BookingSerializer(booking).data, message="Escrow released")
                
            return failure_response(message="Invalid action name")
            
        except ValueError as e:
            return failure_response(message=str(e))


class MatchTravellerListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        shipment_id = self.kwargs.get('shipment_id')
        return MatchingService.find_compatible_trips_for_shipment(shipment_id)
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Compatible travellers found")

class MatchShipmentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ShipmentSerializer

    def get_queryset(self):
        trip_id = self.kwargs.get('trip_id')
        return MatchingService.find_compatible_shipments_for_trip(trip_id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Compatible shipments found")
