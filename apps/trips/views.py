from rest_framework import generics, permissions, status
from django.db.models import Q
from .models import Trip
from .serializers import TripSerializer, TripCreateSerializer
from common.responses import success_response, failure_response
from common.permissions import IsKYCApproved

class TripListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TripCreateSerializer
        return TripSerializer

    def get_queryset(self):
        from django.db.models import Count
        queryset = Trip.objects.all().select_related('user', 'user__profile').annotate(bookings_count_annotated=Count('bookings'))
        
        # Filter for admin overview, user only, or active sender searches
        admin_all = self.request.query_params.get('admin_all', 'false').lower() == 'true'
        user_only = self.request.query_params.get('user_only', 'false').lower() == 'true'
        
        if admin_all and (self.request.user.role == 'admin' or self.request.user.is_staff):
            pass  # Admins can view all trips (Active, Completed, Cancelled)
        elif user_only:
            queryset = queryset.filter(user=self.request.user)
        else:
            # Senders search active trips
            queryset = queryset.filter(status='Active')

        # Filter criteria
        from_loc = self.request.query_params.get('from')
        to_loc = self.request.query_params.get('to')
        dep_date = self.request.query_params.get('date')

        if from_loc:
            queryset = queryset.filter(from_location__icontains=from_loc)
        if to_loc:
            queryset = queryset.filter(to_location__icontains=to_loc)
        if dep_date:
            queryset = queryset.filter(departure_date=dep_date)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Trips retrieved successfully")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.save(user=request.user)
            
            # Sync to LuggageListing model
            try:
                from apps.luggage_sharing.models import LuggageListing
                from decimal import Decimal
                LuggageListing.objects.create(
                    owner=request.user,
                    airline=trip.airline if trip.airline and trip.airline != 'TRAVELER_TRIP' else 'Custom Flight',
                    flight_number=trip.flight_number or 'TRIP',
                    departure_airport=trip.from_location or 'N/A',
                    arrival_airport=trip.to_location or 'N/A',
                    departure_date=trip.departure_date,
                    departure_time=trip.departure_time or '12:00:00',
                    cabin_class='Economy',
                    max_airline_allowance=trip.available_weight or Decimal('20.00'),
                    currently_used_weight=Decimal('0.00'),
                    available_weight=trip.available_weight or Decimal('20.00'),
                    price_per_kg=trip.price_per_kg or Decimal('15.00'),
                    min_kg=Decimal('1.00'),
                    max_kg=trip.available_weight or Decimal('20.00'),
                    accept_partial_booking=True,
                    instant_booking=True,
                    insurance=True,
                    description=f'Trip from {trip.from_location} to {trip.to_location}',
                    status='ACTIVE'
                )
            except Exception as e:
                print("Error syncing LuggageListing:", e)

            full_data = TripSerializer(trip).data
            return success_response(data=full_data, message="Trip registered successfully", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to create trip")

class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsKYCApproved]
    serializer_class = TripSerializer
    queryset = Trip.objects.all().select_related('user')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Trip details fetched")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Verify ownership or admin status
        if instance.user != request.user and request.user.role != 'admin' and not request.user.is_staff:
            return failure_response(message="You do not have permission to modify this trip", status_code=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="Trip updated successfully")
        return failure_response(errors=serializer.errors, message="Failed to update trip")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Verify ownership or admin status
        if instance.user != request.user and request.user.role != 'admin' and not request.user.is_staff:
            return failure_response(message="You do not have permission to delete this trip", status_code=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return success_response(message="Trip deleted successfully")
