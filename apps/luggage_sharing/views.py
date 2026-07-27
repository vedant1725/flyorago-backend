from decimal import Decimal
import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum, Q, Avg
from django.utils import timezone
from notifications.models import Notification

from .models import (
    LuggageListing, LuggageBooking, LuggageVerification,
    LuggageQRLog, LuggageOTPLog, LuggageTracking,
    LuggageReview, LuggageDispute
)
from .serializers import (
    LuggageListingSerializer, LuggageBookingSerializer,
    LuggageVerificationSerializer, LuggageQRLogSerializer,
    LuggageOTPLogSerializer, LuggageTrackingSerializer,
    LuggageReviewSerializer, LuggageDisputeSerializer
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

        user_listings = LuggageListing.objects.filter(owner=user)
        total_shared_weight = user_listings.aggregate(s=Sum('max_airline_allowance'))['s'] or Decimal('0.00')
        available_weight = user_listings.filter(status='ACTIVE').aggregate(s=Sum('available_weight'))['s'] or Decimal('0.00')

        bookings = LuggageBooking.objects.filter(Q(owner=user) | Q(booker=user))
        
        earnings = bookings.filter(owner=user, status='COMPLETED').aggregate(s=Sum('total_price'))['s'] or Decimal('0.00')
        active_sharing = bookings.filter(status__in=['ACCEPTED', 'PAID', 'VERIFIED', 'IN_TRANSIT', 'ARRIVED']).count()
        pending_requests = bookings.filter(status='REQUESTED').count()
        completed_sharing = bookings.filter(status='COMPLETED').count()

        avg_rating = LuggageReview.objects.filter(reviewee=user).aggregate(a=Avg('rating'))['a'] or Decimal('4.90')
        current_trips = LuggageListingSerializer(user_listings.filter(status='ACTIVE'), many=True).data

        return Response({
            'status': 'success',
            'current_user_id': user.id,
            'current_user_email': user.email,
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
        return Response({
            'status': 'success',
            'current_user_id': request.user.id,
            'current_user_email': request.user.email,
            'data': serializer.data
        })

    def post(self, request):
        serializer = LuggageListingSerializer(data=request.data)
        if serializer.is_valid():
            listing = serializer.save(owner=request.user)
            
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
        dep_airport = request.data.get('departure_airport', '').strip()
        arr_airport = request.data.get('arrival_airport', '').strip()
        airline = request.data.get('airline', '').strip()
        flight_number = request.data.get('flight_number', '').strip()
        flight_date = request.data.get('departure_date', '').strip()
        needed_kg = Decimal(str(request.data.get('needed_kg', 1.0)))
        max_price = request.data.get('max_price')

        today = timezone.now().date()
        listings = LuggageListing.objects.filter(
            status='ACTIVE',
            available_weight__gte=needed_kg,
            departure_date__gte=today
        )

        # MARKETPLACE RULE: Owner MUST NEVER see his own listing inside search results
        if request.user and request.user.is_authenticated:
            listings = listings.exclude(owner=request.user)

        if dep_airport:
            listings = listings.filter(departure_airport__icontains=dep_airport)
        if arr_airport:
            listings = listings.filter(arrival_airport__icontains=arr_airport)
        if airline:
            listings = listings.filter(airline__icontains=airline)
        if flight_number:
            listings = listings.filter(flight_number__icontains=flight_number)
        if flight_date:
            listings = listings.filter(departure_date=flight_date)
        if max_price:
            listings = listings.filter(price_per_kg__lte=Decimal(str(max_price)))

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

        sort_by = request.data.get('sort_by', 'best_match')
        if sort_by == 'lowest_price':
            results.sort(key=lambda x: float(x['price_per_kg']))
        elif sort_by == 'most_weight':
            results.sort(key=lambda x: float(x['available_weight']), reverse=True)
        else:
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

        return Response({
            'status': 'success',
            'current_user_id': user.id,
            'current_user_email': user.email,
            'data': LuggageBookingSerializer(bookings, many=True).data
        })

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

        booking = LuggageBooking.objects.create(
            listing=listing,
            booker=request.user,
            owner=listing.owner,
            booked_weight=booked_weight,
            price_per_kg=price_per_kg,
            total_price=final_total,
            insurance_fee=insurance_fee,
            status='REQUESTED',
            notes=notes
        )

        Notification.objects.create(
            user=listing.owner,
            title='Luggage Sharing Request Received',
            message=f'{request.user.get_full_name() or request.user.email} sent a request for {booked_weight}kg on {listing.airline} {listing.flight_number}.',
            type='booking'
        )

        return Response({
            'status': 'success',
            'message': 'Luggage sharing request created successfully!',
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

        user = request.user

        if action == 'accept':
            # Allow owner or admin or testing
            booking.status = 'ACCEPTED'
            booking.save()

            listing = booking.listing
            listing.currently_used_weight += booking.booked_weight
            listing.save()

            Notification.objects.create(
                user=booking.booker,
                title='Luggage Request Approved',
                message=f'Your luggage request for {booking.booked_weight}kg has been approved! Proceed to payment.',
                type='booking'
            )

        elif action == 'reject':
            booking.status = 'REJECTED'
            booking.save()

            if booking.escrow_status == 'HELD':
                process_luggage_escrow_refund(booking)

            Notification.objects.create(
                user=booking.booker,
                title='Luggage Request Rejected',
                message=f'Your luggage request for booking #{booking.id} was declined.'
            )

        elif action == 'pay':
            if booking.status != 'ACCEPTED':
                return Response({'status': 'error', 'message': 'Payment is only available after request is approved.'}, status=status.HTTP_400_BAD_REQUEST)

            booking.status = 'PAID'
            booking.escrow_status = 'HELD'
            booking.save()

            process_luggage_escrow_hold(booking)

            Notification.objects.create(
                user=booking.owner,
                title='Luggage Payment Received',
                message=f'Payment of ${booking.total_price} for Booking #{booking.id} has been secured in escrow.'
            )

        elif action == 'verify_luggage':
            images = request.data.get('bag_images', '[]')
            weight = Decimal(str(request.data.get('weight', booking.booked_weight)))
            notes = request.data.get('notes', '')
            lat = request.data.get('latitude')
            lng = request.data.get('longitude')
            is_appr = request.data.get('is_approved', True)

            verif = LuggageVerification.objects.create(
                booking=booking,
                verified_by=user,
                bag_images=images,
                weight=weight,
                notes=notes,
                latitude=lat,
                longitude=lng,
                is_approved=is_appr
            )

            if is_appr:
                booking.status = 'VERIFIED'
            else:
                booking.status = 'VERIFICATION_REJECTED'
            booking.save()

            Notification.objects.create(
                user=booking.booker,
                title='Luggage Verified',
                message=f'Luggage for Booking #{booking.id} was verified by traveller.',
                type='booking'
            )

        elif action == 'start_transit':
            booking.status = 'IN_TRANSIT'
            booking.save()

            LuggageTracking.objects.create(
                booking=booking,
                status='IN_TRANSIT',
                location_name=booking.listing.departure_airport,
                notes='Luggage checked in and flight in transit.'
            )

            Notification.objects.create(
                user=booking.booker,
                title='Luggage In Transit',
                message=f'Booking #{booking.id} is now in transit.',
                type='booking'
            )

        elif action == 'arrived':
            booking.status = 'ARRIVED'
            booking.save()

            LuggageTracking.objects.create(
                booking=booking,
                status='ARRIVED',
                location_name=booking.listing.arrival_airport,
                notes='Flight arrived at destination airport.'
            )

            Notification.objects.create(
                user=booking.booker,
                title='Traveller Arrived',
                message=f'Traveller has arrived for Booking #{booking.id}. Please present your QR or OTP for pickup.',
                type='booking'
            )

        elif action == 'verify_qr':
            qr_token = request.data.get('qr_code_token', '').strip()
            is_valid = (qr_token.upper() == booking.qr_code_token.upper())

            LuggageQRLog.objects.create(
                booking=booking,
                scanned_by=user,
                qr_token=qr_token,
                is_success=is_valid,
                notes='QR Scan verification attempt'
            )

            if not is_valid:
                return Response({'status': 'error', 'message': 'Invalid QR Code token.'}, status=status.HTTP_400_BAD_REQUEST)

            booking.status = 'COMPLETED'
            booking.escrow_status = 'RELEASED'
            booking.save()

            process_luggage_escrow_release(booking)

            Notification.objects.create(
                user=booking.owner,
                title='Sharing Completed & Payment Released 🎉',
                message=f'Booking #{booking.id} QR verified! ${booking.total_price} released to your wallet.'
            )

        elif action == 'verify_otp':
            otp_input = request.data.get('otp', '').strip()
            is_valid = (otp_input == booking.otp_code)

            LuggageOTPLog.objects.create(
                booking=booking,
                entered_by=user,
                otp_entered=otp_input,
                is_success=is_valid
            )

            if not is_valid:
                return Response({'status': 'error', 'message': 'Invalid OTP Code.'}, status=status.HTTP_400_BAD_REQUEST)

            booking.status = 'COMPLETED'
            booking.escrow_status = 'RELEASED'
            booking.save()

            process_luggage_escrow_release(booking)

            Notification.objects.create(
                user=booking.owner,
                title='Sharing Completed & Payment Released 🎉',
                message=f'Booking #{booking.id} OTP verified! ${booking.total_price} released to your wallet.'
            )

        return Response({
            'status': 'success',
            'message': f'Booking status updated to {booking.status}',
            'data': LuggageBookingSerializer(booking).data
        })


class LuggageQRVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        qr_scanned = request.data.get('qr_code_token', '').strip()
        booking = None
        if pk and str(pk) != '0':
            booking = LuggageBooking.objects.filter(pk=pk).first()

        if not booking and qr_scanned:
            booking = LuggageBooking.objects.filter(qr_code_token__iexact=qr_scanned).first()

        if not booking:
            return Response({'status': 'error', 'message': f'Booking for QR Token "{qr_scanned}" not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_valid = (qr_scanned.upper() == booking.qr_code_token.upper())
        LuggageQRLog.objects.create(
            booking=booking,
            scanned_by=request.user,
            qr_token=qr_scanned,
            is_success=is_valid
        )

        if not is_valid:
            return Response({'status': 'error', 'message': 'Invalid QR token.'}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'COMPLETED'
        booking.escrow_status = 'RELEASED'
        booking.save()

        process_luggage_escrow_release(booking)

        return Response({
            'status': 'success',
            'message': f'QR Code Verified for Booking #{booking.id}! Escrow released.',
            'data': LuggageBookingSerializer(booking).data
        })


class LuggageRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        rating_val = Decimal(str(request.data.get('rating', '5.0')))
        comment = request.data.get('comment', '')

        try:
            booking = LuggageBooking.objects.get(pk=booking_id)
        except LuggageBooking.DoesNotExist:
            return Response({'status': 'error', 'message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        reviewee = booking.owner if request.user == booking.booker else booking.booker

        review = LuggageReview.objects.create(
            booking=booking,
            reviewer=request.user,
            reviewee=reviewee,
            rating=rating_val,
            behaviour_score=int(request.data.get('behaviour_score', 5)),
            communication_score=int(request.data.get('communication_score', 5)),
            timing_score=int(request.data.get('timing_score', 5)),
            experience_score=int(request.data.get('experience_score', 5)),
            comment=comment
        )

        return Response({'status': 'success', 'data': LuggageReviewSerializer(review).data})


class LuggageDisputeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get('booking_id')
        reason = request.data.get('reason')
        description = request.data.get('description')

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
            status='OPEN'
        )

        return Response({'status': 'success', 'message': 'Dispute created.', 'data': LuggageDisputeSerializer(dispute).data})


class LuggageAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        listings = LuggageListing.objects.all()[:50]
        bookings = LuggageBooking.objects.all()[:50]
        disputes = LuggageDispute.objects.all()[:30]
        verifications = LuggageVerification.objects.all()[:30]
        qr_logs = LuggageQRLog.objects.all()[:30]
        otp_logs = LuggageOTPLog.objects.all()[:30]

        return Response({
            'status': 'success',
            'data': {
                'listings': LuggageListingSerializer(listings, many=True).data,
                'requests': LuggageBookingSerializer(bookings.filter(status='REQUESTED'), many=True).data,
                'active_sharing': LuggageBookingSerializer(bookings.filter(status__in=['ACCEPTED', 'PAID', 'VERIFIED', 'IN_TRANSIT', 'ARRIVED']), many=True).data,
                'completed_sharing': LuggageBookingSerializer(bookings.filter(status='COMPLETED'), many=True).data,
                'disputes': LuggageDisputeSerializer(disputes, many=True).data,
                'payments': LuggageBookingSerializer(bookings.filter(escrow_status__in=['HELD', 'RELEASED']), many=True).data,
                'verifications': LuggageVerificationSerializer(verifications, many=True).data,
                'qr_logs': LuggageQRLogSerializer(qr_logs, many=True).data,
                'otp_logs': LuggageOTPLogSerializer(otp_logs, many=True).data,
            }
        })

    def post(self, request):
        action = request.data.get('action')
        listing_id = request.data.get('listing_id')

        try:
            listing = LuggageListing.objects.get(pk=listing_id)
        except LuggageListing.DoesNotExist:
            return Response({'status': 'error', 'message': 'Listing not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'suspend':
            listing.status = 'SUSPENDED'
            listing.save()
            return Response({'status': 'success', 'message': f'Listing #{listing.id} suspended.'})
        elif action == 'delete':
            listing.status = 'CANCELLED'
            listing.save()
            return Response({'status': 'success', 'message': f'Listing #{listing.id} deleted.'})

        return Response({'status': 'error', 'message': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
