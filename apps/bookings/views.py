from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer, BookingActionRequestSerializer
from trips.models import Trip
from common.responses import success_response, failure_response


class BookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

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
                status='Pending'
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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingActionRequestSerializer

    @extend_schema(request=BookingActionRequestSerializer, responses={200: BookingSerializer})
    @transaction.atomic
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        action = request.data.get('action')

        if not action:
            return failure_response(message="Action is required")

        # Authorization Checks
        is_sender = (booking.sender == request.user)
        is_traveler = (booking.traveler == request.user)
        is_admin = (request.user.role == 'admin' or request.user.is_staff)

        if not is_sender and not is_traveler and not is_admin:
            return failure_response(message="Unauthorized action", status_code=status.HTTP_403_FORBIDDEN)

        if action == 'ACCEPT':
            if not is_traveler and not is_admin:
                return failure_response(message="Only the traveler or admin can accept a booking")
            if booking.status != 'Pending' and not is_admin:
                return failure_response(message="Can only accept pending bookings")
            booking.status = 'Accepted'
            booking.save()
            return success_response(data=BookingSerializer(booking).data, message="Booking accepted")

        elif action == 'REJECT':
            if not is_traveler and not is_admin:
                return failure_response(message="Only the traveler or admin can reject a booking")
            if booking.status != 'Pending' and not is_admin:
                return failure_response(message="Can only reject pending bookings")
            booking.status = 'Rejected'
            # Release trip weight allocation
            if booking.trip:
                booking.trip.available_weight += booking.weight
                booking.trip.save()
            booking.save()
            return success_response(data=BookingSerializer(booking).data, message="Booking rejected")

        elif action == 'CANCEL':
            if booking.status not in ['Pending', 'Accepted'] and not is_admin:
                return failure_response(message="Cannot cancel booking at this stage")
            booking.status = 'Cancelled'
            # Release trip weight allocation
            if booking.trip:
                booking.trip.available_weight += booking.weight
                booking.trip.save()
            booking.save()
            return success_response(data=BookingSerializer(booking).data, message="Booking cancelled")

        elif action == 'DEPOSIT_ESCROW':
            if not is_sender and not is_admin:
                return failure_response(message="Only the sender or admin can deposit funds")
            if booking.status != 'Accepted' and not is_admin:
                return failure_response(message="Can only fund accepted bookings")
            booking.payment_status = 'Escrow Hold'
            booking.escrow_status = 'Active Hold'
            booking.save()
            
            # In a real wallet flow, record a transaction. Covered in wallet/payments apps.
            return success_response(data=BookingSerializer(booking).data, message="Funds deposited to Escrow")

        elif action == 'RELEASE_ESCROW':
            if booking.status != 'Delivered' and not is_admin:
                return failure_response(message="Can only release escrow for delivered packages")
            booking.status = 'Completed'
            booking.payment_status = 'Released'
            booking.escrow_status = 'Released'
            booking.save()

            # Record completed trip statistics
            try:
                profile = booking.traveler.profile
                profile.completed_trips += 1
                profile.save()
            except Exception:
                pass
                
            return success_response(data=BookingSerializer(booking).data, message="Escrow released successfully")

        return failure_response(message="Invalid action name")
