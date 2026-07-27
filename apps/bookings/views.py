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
            
            # Reduce trip weight
            trip.available_weight -= weight
            trip.save()

            booking = serializer.save(
                sender=request.user,
                traveler=trip.user,
                status='REQUEST_SENT'
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
                input_otp = str(request.data.get('otp') or request.data.get('delivery_otp') or '').strip()
                booking = BookingWorkflowService.complete_delivery(booking, input_otp)
                
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
