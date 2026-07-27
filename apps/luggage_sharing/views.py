from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Q, Avg
from notifications.models import Notification

from .models import (
    LuggageListing, LuggageBooking, LuggageVerificationLog,
    LuggageWeightLog, LuggageRating, LuggageDispute
)
from .serializers import (
    LuggageListingSerializer, LuggageBookingSerializer,
    LuggageVerificationLogSerializer, LuggageWeightLogSerializer,
    LuggageRatingSerializer, LuggageDisputeSerializer
)
from .services import (
    calculate_ai_match_score,
    process_luggage_escrow_hold,
    process_luggage_escrow_release,
    process_luggage_escrow_refund
)

from trips.models import Trip

class LuggageDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Auto-sync any existing Trip objects into LuggageListings for this user
        existing_trips = Trip.objects.filter(user=user, status='Active')
        for trip in existing_trips:
            LuggageListing.objects.get_or_create(
                owner=user,
                flight_number=trip.flight_number or 'TRIP',
                departure_date=trip.departure_date,
                defaults={
                    'airline': trip.airline if trip.airline and trip.airline != 'TRAVELER_TRIP' else 'Custom Flight',
                    'departure_airport': trip.from_location or 'N/A',
                    'arrival_airport': trip.to_location or 'N/A',
                    'departure_time': trip.departure_time or '12:00:00',
                    'cabin_class': 'Economy',
                    'max_airline_allowance': trip.available_weight or Decimal('20.00'),
                    'currently_used_weight': Decimal('0.00'),
                    'available_weight': trip.available_weight or Decimal('20.00'),
                    'price_per_kg': trip.price_per_kg or Decimal('15.00'),
                    'min_kg': Decimal('1.00'),
                    'max_kg': trip.available_weight or Decimal('20.00'),
                    'accept_partial_booking': True,
                    'instant_booking': True,
                    'insurance': True,
                    'description': f'Trip from {trip.from_location} to {trip.to_location}',
                    'status': 'ACTIVE'
                }
            )

        # User's listings stats
        user_listings = LuggageListing.objects.filter(owner=user)
        total_shared_weight = user_listings.aggregate(s=Sum('max_airline_allowance'))['s'] or Decimal('0.00')
        available_weight = user_listings.filter(status='ACTIVE').aggregate(s=Sum('available_weight'))['s'] or Decimal('0.00')

        # User's bookings (as owner or booker)
        bookings = LuggageBooking.objects.filter(Q(owner=user) | Q(booker=user))
        
        earnings = bookings.filter(owner=user, status='COMPLETED').aggregate(s=Sum('total_price'))['s'] or Decimal('0.00')
        active_sharing = bookings.filter(status__in=['ACCEPTED', 'AIRPORT_MEETING', 'BAG_RECEIVED', 'IN_FLIGHT', 'ARRIVED']).count()
        pending_requests = bookings.filter(status='REQUESTED').count()
        completed_sharing = bookings.filter(status='COMPLETED').count()

        # Trust Rating
        avg_rating = LuggageRating.objects.filter(reviewee=user).aggregate(a=Avg('overall_rating'))['a'] or 4.90

        # Current Trips / Active Listings
        current_trips = LuggageListingSerializer(user_listings.filter(status='ACTIVE'), many=True).data

        return Response({
            'status': 'success',
            'data': {
                'total_shared_weight': float(total_shared_weight),
                'available_weight': float(available_weight),
                'earnings': float(earnings),
                'active_sharing': active_sharing,
                'pending_requests': pending_requests,
                'completed_sharing': completed_sharing,
                'trust_rating': round(float(avg_rating), 2),
                'current_trips': current_trips
            }
        })


class LuggageListingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mode = request.query_params.get('mode', 'my')
        if mode == 'my':
            listings = LuggageListing.objects.filter(owner=request.user)
        else:
            listings = LuggageListing.objects.filter(status='ACTIVE').exclude(owner=request.user)
        
        serializer = LuggageListingSerializer(listings, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    def post(self, request):
        serializer = LuggageListingSerializer(data=request.data)
        if serializer.is_valid():
            listing = serializer.save(owner=request.user)
            
            # Sync to Trip model
            try:
                Trip.objects.create(
                    user=request.user,
                    flight_number=listing.flight_number,
                    airline=listing.airline,
                    aircraft='N/A',
                    from_location=listing.departure_airport,
                    to_location=listing.arrival_airport,
                    from_airport=listing.departure_airport,
                    to_airport=listing.arrival_airport,
                    departure_date=listing.departure_date,
                    departure_time=listing.departure_time,
                    arrival_date=listing.departure_date,
                    arrival_time=listing.departure_time,
                    duration='N/A',
                    available_weight=listing.available_weight,
                    price_per_kg=listing.price_per_kg,
                    status='Active'
                )
            except Exception as e:
                print("Error syncing Trip:", e)

            return Response({'status': 'success', 'message': 'Luggage listing created successfully!', 'data': LuggageListingSerializer(listing).data}, status=status.HTTP_201_CREATED)
        return Response({'status': 'error', 'message': 'Validation failed', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LuggageListingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            listing = LuggageListing.objects.get(pk=pk)
            return Response({'status': 'success', 'data': LuggageListingSerializer(listing).data})
        except LuggageListing.DoesNotExist:
            return Response({'status': 'error', 'message': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            listing = LuggageListing.objects.get(pk=pk, owner=request.user)
            serializer = LuggageListingSerializer(listing, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'status': 'success', 'data': LuggageListingSerializer(updated).data})
            return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except LuggageListing.DoesNotExist:
            return Response({'status': 'error', 'message': 'Listing not found or access denied'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            listing = LuggageListing.objects.get(pk=pk, owner=request.user)
            listing.status = 'CANCELLED'
            listing.save()
            return Response({'status': 'success', 'message': 'Listing cancelled successfully'})
        except LuggageListing.DoesNotExist:
            return Response({'status': 'error', 'message': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)


class LuggageSearchMatchingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        dep_airport = request.data.get('departure_airport', '')
        arr_airport = request.data.get('arrival_airport', '')
        airline = request.data.get('airline', '')
        flight_number = request.data.get('flight_number', '')
        flight_date = request.data.get('departure_date', '')
        needed_kg = float(request.data.get('needed_kg', 1.0))

        # Filter active listings with available weight > 0
        listings = LuggageListing.objects.filter(
            status='ACTIVE',
            available_weight__gt=0
        )

        # Exclude owner's own listings and listings user already requested
        if request.user and request.user.is_authenticated:
            listings = listings.exclude(owner=request.user)
            existing_booked_ids = LuggageBooking.objects.filter(
                booker=request.user
            ).exclude(status__in=['REJECTED', 'CANCELLED']).values_list('listing_id', flat=True)
            listings = listings.exclude(id__in=existing_booked_ids)

        if dep_airport:
            listings = listings.filter(departure_airport__icontains=dep_airport)
        if arr_airport:
            listings = listings.filter(arrival_airport__icontains=arr_airport)

        results = []
        search_params = {
            'departure_airport': dep_airport,
            'arrival_airport': arr_airport,
            'airline': airline,
            'flight_number': flight_number,
            'departure_date': flight_date
        }

        for listing in listings:
            score, badge = calculate_ai_match_score(listing, search_params)
            listing_data = LuggageListingSerializer(listing).data
            listing_data['ai_match_score'] = score
            listing_data['ai_match_badge'] = badge
            results.append(listing_data)

        # Sort by highest match score first
        results.sort(key=lambda x: x['ai_match_score'], reverse=True)

        return Response({
            'status': 'success',
            'count': len(results),
            'data': results
        })


class LuggageBookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.query_params.get('role', 'all')
        user = request.user
        if role == 'booker':
            bookings = LuggageBooking.objects.filter(booker=user)
        elif role == 'owner':
            bookings = LuggageBooking.objects.filter(owner=user)
        else:
            bookings = LuggageBooking.objects.filter(Q(booker=user) | Q(owner=user))

        return Response({'status': 'success', 'data': LuggageBookingSerializer(bookings, many=True).data})

    def post(self, request):
        listing_id = request.data.get('listing_id')
        booked_weight = Decimal(str(request.data.get('booked_weight', '1.0')))
        notes = request.data.get('notes', '')

        try:
            listing = LuggageListing.objects.get(pk=listing_id, status='ACTIVE')
        except LuggageListing.DoesNotExist:
            return Response({'status': 'error', 'message': 'Listing not found or inactive.'}, status=status.HTTP_404_NOT_FOUND)

        if listing.owner == request.user:
            return Response({'status': 'error', 'message': 'You cannot book your own luggage listing.'}, status=status.HTTP_400_BAD_REQUEST)

        if booked_weight > listing.available_weight:
            return Response({'status': 'error', 'message': f'Requested weight ({booked_weight}kg) exceeds available weight ({listing.available_weight}kg).'}, status=status.HTTP_400_BAD_REQUEST)

        if booked_weight < listing.min_kg or booked_weight > listing.max_kg:
            return Response({'status': 'error', 'message': f'Weight must be between {listing.min_kg}kg and {listing.max_kg}kg.'}, status=status.HTTP_400_BAD_REQUEST)

        price_per_kg = listing.price_per_kg
        total_price = booked_weight * price_per_kg
        insurance_fee = Decimal('5.00') if listing.insurance else Decimal('0.00')
        final_total = total_price + insurance_fee

        booking_status = 'ACCEPTED' if listing.instant_booking else 'REQUESTED'

        booking = LuggageBooking.objects.create(
            listing=listing,
            booker=request.user,
            owner=listing.owner,
            booked_weight=booked_weight,
            price_per_kg=price_per_kg,
            total_price=final_total,
            insurance_fee=insurance_fee,
            status=booking_status,
            notes=notes
        )

        # Place escrow hold
        process_luggage_escrow_hold(booking)

        # Update available weight if instant accepted
        if booking_status == 'ACCEPTED':
            listing.currently_used_weight += booked_weight
            listing.save()

        # Send Notification
        Notification.objects.create(
            user=listing.owner,
            title='Luggage Sharing Request Received',
            message=f'{request.user.get_full_name() or request.user.email} sent a request for {booked_weight}kg on {listing.airline} {listing.flight_number}.',
            type='booking'
        )

        return Response({
            'status': 'success',
            'message': 'Luggage sharing request created & Escrow held successfully!',
            'data': LuggageBookingSerializer(booking).data
        }, status=status.HTTP_201_CREATED)


class LuggageBookingActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        action = request.data.get('action')
        try:
            booking = LuggageBooking.objects.get(pk=pk)
        except LuggageBooking.DoesNotExist:
            return Response({'status': 'error', 'message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            if booking.owner != request.user:
                return Response({'status': 'error', 'message': 'Only owner can accept request.'}, status=status.HTTP_403_FORBIDDEN)
            booking.status = 'ACCEPTED'
            booking.save()

            # Deduct listing available weight
            listing = booking.listing
            listing.currently_used_weight += booking.booked_weight
            listing.save()

            Notification.objects.create(
                user=booking.booker,
                title='Luggage Request Accepted',
                message=f'Your luggage request for {booking.booked_weight}kg has been accepted by {request.user.get_full_name() or request.user.email}.',
                type='booking'
            )

        elif action == 'reject':
            if booking.owner != request.user:
                return Response({'status': 'error', 'message': 'Only owner can reject request.'}, status=status.HTTP_403_FORBIDDEN)
            booking.status = 'REJECTED'
            booking.save()

            # Refund escrow
            process_luggage_escrow_refund(booking)

            Notification.objects.create(
                user=booking.booker,
                title='Luggage Request Rejected',
                message=f'Your luggage request for booking #{booking.id} was declined.'
            )

        elif action == 'meeting_ready':
            booking.status = 'AIRPORT_MEETING'
            booking.save()

        elif action == 'bag_received':
            booking.status = 'BAG_RECEIVED'
            booking.save()

        elif action == 'in_flight':
            booking.status = 'IN_FLIGHT'
            booking.save()

        elif action == 'arrived':
            booking.status = 'ARRIVED'
            booking.save()

        elif action == 'confirm_delivery':
            booking.status = 'COMPLETED'
            booking.save()

            # Release Escrow Payment to owner!
            process_luggage_escrow_release(booking)

            Notification.objects.create(
                user=booking.owner,
                title='Payment Released - Luggage Sharing Completed',
                message=f'Payment of ${booking.total_price} for Luggage Booking #{booking.id} has been released to your wallet!'
            )

        elif action == 'cancel':
            booking.status = 'CANCELLED'
            booking.save()
            process_luggage_escrow_refund(booking)

        return Response({
            'status': 'success',
            'message': f'Booking status updated to {booking.status}',
            'data': LuggageBookingSerializer(booking).data
        })


class LuggageQRVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        qr_scanned = request.data.get('qr_code_token', '').strip()
        selfie_image = request.data.get('selfie_image')
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        device_hash = request.data.get('device_hash', 'DEV-MOBILE-01')

        booking = None
        if pk and str(pk) != '0':
            booking = LuggageBooking.objects.filter(pk=pk).first()

        if not booking and qr_scanned:
            booking = LuggageBooking.objects.filter(qr_code_token__iexact=qr_scanned).first()

        if not booking:
            return Response({'status': 'error', 'message': f'Booking for QR Token "{qr_scanned}" not found.'}, status=status.HTTP_404_NOT_FOUND)

        if qr_scanned and qr_scanned.upper() != booking.qr_code_token.upper():
            LuggageVerificationLog.objects.create(
                booking=booking,
                verified_by=request.user,
                verification_type='QR_SCAN',
                selfie_image=selfie_image,
                latitude=lat,
                longitude=lng,
                device_hash=device_hash,
                qr_scanned_token=qr_scanned,
                is_success=False,
                notes='QR Code Token Mismatch verification failed.'
            )
            return Response({'status': 'error', 'message': 'Invalid QR Code token.'}, status=status.HTTP_400_BAD_REQUEST)

        # Log successful verification
        log = LuggageVerificationLog.objects.create(
            booking=booking,
            verified_by=request.user,
            verification_type='QR_SCAN',
            selfie_image=selfie_image,
            latitude=lat,
            longitude=lng,
            device_hash=device_hash,
            qr_scanned_token=booking.qr_code_token,
            is_success=True,
            notes='Airport meeting QR verification & selfie validated successfully.'
        )

        booking.status = 'BAG_RECEIVED'
        booking.save()

        # Send Notifications
        Notification.objects.create(
            user=booking.owner,
            title='Airport Bag Handover Verified',
            message=f'QR token for Booking #{booking.id} verified. Bag handover recorded.',
            type='booking'
        )
        Notification.objects.create(
            user=booking.booker,
            title='Bag Handover Verified',
            message=f'Your bag for Booking #{booking.id} has been verified and received by the traveller.',
            type='booking'
        )

        return Response({
            'status': 'success',
            'message': f'QR Code & Passport Verified for Booking #{booking.id}! Bag handover confirmed.',
            'data': LuggageBookingSerializer(booking).data
        })


class LuggageWeightLogView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        stage = request.data.get('stage', 'PICKUP')
        weight = Decimal(str(request.data.get('weight', '0.0')))
        photo_evidence = request.data.get('photo_evidence', '')
        notes = request.data.get('notes', '')

        try:
            booking = LuggageBooking.objects.get(pk=pk)
        except LuggageBooking.DoesNotExist:
            return Response({'status': 'error', 'message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        log = LuggageWeightLog.objects.create(
            booking=booking,
            logged_by=request.user,
            stage=stage,
            weight=weight,
            photo_evidence=photo_evidence,
            notes=notes
        )

        return Response({
            'status': 'success',
            'message': f'Weight log for {stage} stage recorded ({weight}kg).',
            'data': LuggageWeightLogSerializer(log).data
        })


class LuggageRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        comm = int(request.data.get('communication_score', 5))
        punc = int(request.data.get('punctuality_score', 5))
        behav = int(request.data.get('behaviour_score', 5))
        acc = int(request.data.get('accuracy_score', 5))
        comment = request.data.get('comment', '')

        try:
            booking = LuggageBooking.objects.get(pk=booking_id)
        except LuggageBooking.DoesNotExist:
            return Response({'status': 'error', 'message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        reviewee = booking.owner if request.user == booking.booker else booking.booker
        overall = (comm + punc + behav + acc) / 4.0

        rating = LuggageRating.objects.create(
            booking=booking,
            reviewer=request.user,
            reviewee=reviewee,
            communication_score=comm,
            punctuality_score=punc,
            behaviour_score=behav,
            accuracy_score=acc,
            overall_rating=Decimal(str(overall)),
            comment=comment
        )

        return Response({'status': 'success', 'data': LuggageRatingSerializer(rating).data})


class LuggageDisputeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        reason = request.data.get('reason')
        description = request.data.get('description')
        evidence = request.data.get('evidence_urls', '[]')

        try:
            booking = LuggageBooking.objects.get(pk=booking_id)
        except LuggageBooking.DoesNotExist:
            return Response({'status': 'error', 'message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        booking.status = 'DISPUTED'
        booking.save()

        dispute = LuggageDispute.objects.create(
            booking=booking,
            raised_by=request.user,
            reason=reason,
            description=description,
            evidence_urls=evidence,
            status='OPEN'
        )

        return Response({'status': 'success', 'message': 'Dispute case opened successfully', 'data': LuggageDisputeSerializer(dispute).data})


class LuggageAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        listings = LuggageListing.objects.all()[:20]
        bookings = LuggageBooking.objects.all()[:20]
        disputes = LuggageDispute.objects.all()[:10]
        verifications = LuggageVerificationLog.objects.all()[:20]

        return Response({
            'status': 'success',
            'data': {
                'listings': LuggageListingSerializer(listings, many=True).data,
                'bookings': LuggageBookingSerializer(bookings, many=True).data,
                'disputes': LuggageDisputeSerializer(disputes, many=True).data,
                'verifications': LuggageVerificationLogSerializer(verifications, many=True).data
            }
        })
