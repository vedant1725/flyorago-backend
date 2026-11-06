import logging
from notifications.services import MultiLevelNotificationEngine
from notifications.models import Notification
from rest_framework import generics, permissions, status, views

logger = logging.getLogger(__name__)
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
        # Retrieve bookings where active user is sender OR traveler with prefetched user profiles
        queryset = Booking.objects.all().select_related(
            'sender', 'sender__profile', 
            'traveler', 'traveler__profile', 
            'trip'
        )
        
        admin_all = self.request.query_params.get('admin_all', 'false').lower() == 'true'
        
        if admin_all and (self.request.user.role == 'admin' or self.request.user.is_staff):
            pass  # Admins can view all bookings in the system
        else:
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
            trip = serializer.validated_data.get('trip')
            weight = serializer.validated_data['weight']

            if trip:
                # Prevent self-matching
                if trip.user == request.user:
                    return failure_response(message="Self-matching is not permitted. You cannot book your own trip.", status_code=status.HTTP_400_BAD_REQUEST)

                # Prevent duplicate active requests
                existing = Booking.objects.filter(
                    sender=request.user,
                    trip=trip,
                    status__in=['REQUEST_SENT', 'ACCEPTED', 'PAID', 'PARCEL_VERIFIED', 'IN_TRANSIT', 'ARRIVED', 'OUT_FOR_DELIVERY']
                ).exists()
                if existing:
                    return failure_response(message="You have already sent an active request for this trip.", status_code=status.HTTP_400_BAD_REQUEST)
                
                # Reduce trip weight
                trip.available_weight -= weight
                trip.save()

            # Automatically calculate reward based on traveler's price_per_kg and parcel weight
            calculated_reward = serializer.validated_data.get('reward', 0)
            if (not calculated_reward or calculated_reward == 0) and trip:
                calculated_reward = weight * trip.price_per_kg

            rec_name = (request.data.get('receiver_name') or request.data.get('receiverName') or serializer.validated_data.get('receiver_name') or '').strip()
            rec_phone = (request.data.get('receiver_phone') or request.data.get('receiverPhone') or serializer.validated_data.get('receiver_phone') or '').strip()
            rec_addr = (request.data.get('receiver_address') or request.data.get('receiverAddress') or serializer.validated_data.get('receiver_address') or '').strip()

            # If sender_trip is linked, pull missing receiver details from it
            sender_trip_obj = serializer.validated_data.get('sender_trip')
            if not sender_trip_obj:
                st_id = request.data.get('sender_trip_id') or request.data.get('sender_trip')
                if st_id:
                    from trips.models import Trip as TripModel
                    sender_trip_obj = TripModel.objects.filter(id=st_id).first()

            if sender_trip_obj:
                if (not rec_name or rec_name.lower() == 'receiver') and sender_trip_obj.terminal_from and sender_trip_obj.terminal_from != 'N/A':
                    rec_name = sender_trip_obj.terminal_from.strip()
                if not rec_phone and sender_trip_obj.terminal_to and sender_trip_obj.terminal_to != 'N/A':
                    rec_phone = sender_trip_obj.terminal_to.strip()
                if not rec_addr and sender_trip_obj.to_location:
                    rec_addr = sender_trip_obj.to_location.strip()
                if sender_trip_obj.notes:
                    try:
                        import json
                        st_notes = json.loads(sender_trip_obj.notes)
                        if isinstance(st_notes, dict):
                            if not rec_name or rec_name.lower() == 'receiver':
                                rec_name = (st_notes.get('receiver_name') or st_notes.get('receiverName') or '').strip()
                            if not rec_phone:
                                rec_phone = (st_notes.get('receiver_phone') or st_notes.get('receiverPhone') or '').strip()
                            if not rec_addr:
                                rec_addr = (st_notes.get('receiver_address') or st_notes.get('receiverAddress') or '').strip()
                    except Exception:
                        pass

            booking = serializer.save(
                sender=request.user,
                traveler=trip.user if trip else None,
                reward=calculated_reward,
                status='REQUEST_SENT' if trip else 'REQUEST_CREATED',
                receiver_name=rec_name,
                receiver_phone=rec_phone,
                receiver_address=rec_addr
            )

            if trip:
                try:
                    MultiLevelNotificationEngine.send_user_notification(
                        user=trip.user,
                        title='New Parcel Delivery Request 📦',
                        message=f'{request.user.first_name or "A Sender"} sent a delivery request for "{booking.package_name}" ({booking.weight} kg).',
                        type='booking'
                    )
                except Exception:
                    pass
            
            full_data = BookingSerializer(booking).data
            return success_response(data=full_data, message="Booking request sent successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to create booking request")

class BookingDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin' or self.request.user.is_staff:
            return Booking.objects.all().select_related('sender', 'traveler', 'trip')
        return Booking.objects.filter(
            Q(sender=self.request.user) | Q(traveler=self.request.user)
        ).select_related('sender', 'traveler', 'trip')

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
                if booking.traveler:
                    MultiLevelNotificationEngine.send_user_notification(
                        user=booking.traveler,
                        title='New Parcel Request Received 📦',
                        message=f'{request.user.first_name or request.user.email} sent a delivery request for "{booking.package_name}" ({booking.weight} kg).',
                        notif_type='booking',
                        extra={'booking_id': booking.id, 'action': 'SEND_REQUEST'}
                    )
                return success_response(data=BookingSerializer(booking).data, message="Booking request sent")

            elif action in ['ACCEPT', 'Accept']:
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can accept")
                booking = BookingWorkflowService.accept_request(booking)
                
                # Notify Sender only
                MultiLevelNotificationEngine.send_user_notification(
                    user=booking.sender,
                    title='Parcel Request Accepted 🎉',
                    message=f'Traveler {request.user.first_name or ""} accepted your request for parcel "{booking.package_name}". Proceed to payment!',
                    notif_type='booking',
                    extra={'booking_id': booking.id, 'action': 'ACCEPT'}
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
                    MultiLevelNotificationEngine.send_user_notification(
                        user=booking.sender,
                        title='Parcel Request Declined ❌',
                        message=f'Traveler declined your request for parcel "{booking.package_name}".',
                        notif_type='booking',
                        extra={'booking_id': booking.id, 'action': 'REJECT'}
                    )
                BookingWorkflowService.trigger_websocket_notification(
                    booking, 'rejected', f"Traveler rejected Booking #{booking.id}."
                )
                return success_response(data=BookingSerializer(booking).data, message="Booking rejected")

            elif action in ['PAY', 'MARK_PAYMENT_COMPLETED', 'DEPOSIT_ESCROW']:
                if not is_sender and not is_admin:
                    return failure_response(message="Only sender can pay")
                payment_method = request.data.get('payment_method') or (request.data.get('payload') or {}).get('payment_method') or 'card'
                try:
                    booking = BookingWorkflowService.process_payment(booking, payment_method=payment_method)
                except ValueError as val_err:
                    return failure_response(message=str(val_err), status_code=status.HTTP_400_BAD_REQUEST)
                # Notify Traveler only
                MultiLevelNotificationEngine.send_user_notification(
                    user=booking.traveler,
                    title='💰 Payment Secured in Escrow!',
                    message=f'{booking.sender.first_name or "Sender"} deposited ₹{booking.reward} into Escrow for "{booking.package_name}". Funds are secured! You can now verify the parcel.',
                    notif_type='payment',
                    extra={'booking_id': booking.id, 'action': 'PAY'}
                )
                return success_response(data=BookingSerializer(booking).data, message="Payment secured in Escrow")

            elif action == 'VERIFY_PARCEL':
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can verify parcel")
                booking = BookingWorkflowService.upload_verification(booking)
                # Notify Sender only
                MultiLevelNotificationEngine.send_user_notification(
                    user=booking.sender,
                    title='Parcel Verified & Picked Up! 📦',
                    message=f'Traveler {booking.traveler.first_name or ""} has verified and picked up your parcel "{booking.package_name}".',
                    notif_type='booking',
                    extra={'booking_id': booking.id, 'action': 'VERIFY_PARCEL'}
                )
                return success_response(data=BookingSerializer(booking).data, message="Parcel verified")

            elif action == 'START_TRANSIT':
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can start transit")
                booking = BookingWorkflowService.update_transit_status(booking, 'IN_TRANSIT')
                # Notify Sender only
                MultiLevelNotificationEngine.send_user_notification(
                    user=booking.sender,
                    title='Luggage In Transit ✈️',
                    message=f'Traveler is now in transit with your parcel "{booking.package_name}".',
                    notif_type='booking',
                    extra={'booking_id': booking.id, 'action': 'START_TRANSIT'}
                )
                return success_response(data=BookingSerializer(booking).data, message="Transit started")

            elif action in ['ARRIVED', 'FLIGHT_LANDED']:
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can mark arrived")
                booking = BookingWorkflowService.update_transit_status(booking, 'ARRIVED')
                # Notify Sender only
                MultiLevelNotificationEngine.send_user_notification(
                    user=booking.sender,
                    title='Traveler Arrived 🛬',
                    message=f'Traveler has arrived at the destination with parcel "{booking.package_name}". Prepare for handover.',
                    notif_type='booking',
                    extra={'booking_id': booking.id, 'action': 'ARRIVED'}
                )
                return success_response(data=BookingSerializer(booking).data, message="Flight arrived")

            elif action == 'OUT_FOR_DELIVERY':
                if not is_traveler and not is_admin:
                    return failure_response(message="Only traveler can mark out for delivery")
                
                # Generate OTP
                calc_otp = str((booking.id * 3791 + 100000) % 900000 + 100000)
                booking.delivery_otp = calc_otp
                
                booking = BookingWorkflowService.update_transit_status(booking, 'OUT_FOR_DELIVERY')
                
                # Notify Sender only
                MultiLevelNotificationEngine.send_user_notification(
                    user=booking.sender,
                    title='Out for Delivery 🚚 OTP Generated',
                    message=f'Your parcel "{booking.package_name}" is out for delivery! Give OTP {booking.delivery_otp} to traveler at handover.',
                    notif_type='booking',
                    extra={'booking_id': booking.id, 'action': 'OUT_FOR_DELIVERY', 'otp': booking.delivery_otp}
                )
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
            logger.warning(f"Booking action ValueError: {e}")
            return failure_response(message=str(e))
        except Exception as e:
            logger.error(f"Booking action {action} failed: {e}", exc_info=True)
            return failure_response(message=f"Action failed: {str(e)}")


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
