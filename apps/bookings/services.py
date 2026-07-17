from django.db.models import Q
from trips.models import Trip
from bookings.models import Booking
from shipments.models import Shipment

class MatchingService:
    @staticmethod
    def find_compatible_trips_for_shipment(shipment_id):
        try:
            shipment = Shipment.objects.select_related('booking__sender').get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Trip.objects.none()

        booking = shipment.booking

        if booking.status != 'Waiting Traveller':
            return Trip.objects.none()

        # Origin and Destination (Basic icontains match for flexibility)
        origin_query = Q(from_location__icontains=shipment.pickup_address) | Q(from_airport__icontains=shipment.pickup_address)
        
        # If pickup_address is long like "New York, NY", we can also do:
        # For simplicity, we assume locations are stored consistently. 
        # But to make it more robust, we check if trip's from_location is in shipment's pickup_address
        
        # Filter Trips
        trips = Trip.objects.filter(
            status='Active',
            available_weight__gte=booking.weight,
            user__profile__kyc_status='APPROVED'
        ).exclude(
            user=booking.sender  # Never match with self
        )
        
        # We perform python-level filtering for icontains to handle cases where 
        # trip.from_location is a substring of shipment.pickup_address and vice versa
        compatible_trips = []
        for trip in trips:
            # Check Origin
            origin_match = (
                trip.from_location.lower() in shipment.pickup_address.lower() or 
                shipment.pickup_address.lower() in trip.from_location.lower() or
                (trip.from_airport and trip.from_airport.lower() in shipment.pickup_address.lower())
            )
            
            # Check Destination
            dest_match = (
                trip.to_location.lower() in shipment.delivery_address.lower() or 
                shipment.delivery_address.lower() in trip.to_location.lower() or
                (trip.to_airport and trip.to_airport.lower() in shipment.delivery_address.lower())
            )
            
            # Check Parcel Type
            # If trip has specific accepted_parcel_types, shipment category must be in it.
            # If empty, accept all.
            type_match = True
            if trip.accepted_parcel_types:
                if shipment.category.lower() not in [t.lower() for t in trip.accepted_parcel_types]:
                    type_match = False
                    
            if origin_match and dest_match and type_match:
                compatible_trips.append(trip.id)
                
        return Trip.objects.filter(id__in=compatible_trips).select_related('user', 'user__profile')

    @staticmethod
    def find_compatible_shipments_for_trip(trip_id):
        try:
            trip = Trip.objects.select_related('user').get(id=trip_id)
        except Trip.DoesNotExist:
            return Shipment.objects.none()

        if trip.status != 'Active' or trip.user.profile.kyc_status != 'APPROVED':
            return Shipment.objects.none()

        bookings = Booking.objects.filter(
            status='Waiting Traveller',
            weight__lte=trip.available_weight
        ).exclude(
            sender=trip.user  # Never match with self
        ).select_related('shipment', 'sender', 'sender__profile')
        
        compatible_shipment_ids = []
        for booking in bookings:
            if not hasattr(booking, 'shipment'):
                continue
            shipment = booking.shipment
            
            # Check Origin
            origin_match = (
                trip.from_location.lower() in shipment.pickup_address.lower() or 
                shipment.pickup_address.lower() in trip.from_location.lower() or
                (trip.from_airport and trip.from_airport.lower() in shipment.pickup_address.lower())
            )
            
            # Check Destination
            dest_match = (
                trip.to_location.lower() in shipment.delivery_address.lower() or 
                shipment.delivery_address.lower() in trip.to_location.lower() or
                (trip.to_airport and trip.to_airport.lower() in shipment.delivery_address.lower())
            )
            
            # Check Parcel Type
            type_match = True
            if trip.accepted_parcel_types:
                if shipment.category.lower() not in [t.lower() for t in trip.accepted_parcel_types]:
                    type_match = False
                    
            if origin_match and dest_match and type_match:
                compatible_shipment_ids.append(shipment.id)
                
        return Shipment.objects.filter(id__in=compatible_shipment_ids).select_related('booking', 'booking__sender')
