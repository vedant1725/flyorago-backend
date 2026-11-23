import uuid
from django.db.models import Q
from django.db import transaction
from trips.models import Trip
from bookings.models import Booking
from shipments.models import Shipment
from wallet.models import Wallet, Transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class MatchingService:
    @staticmethod
    def find_compatible_trips_for_shipment(shipment_id):
        try:
            shipment = Shipment.objects.select_related('booking__sender').get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Trip.objects.none()

        booking = shipment.booking

        if booking.status not in ['Waiting Traveller', 'REQUEST_CREATED']:
            return Trip.objects.none()

        # Origin and Destination (Basic icontains match for flexibility)
        origin_query = Q(from_location__icontains=shipment.pickup_address) | Q(from_airport__icontains=shipment.pickup_address)
        
        # Filter Trips
        trips = Trip.objects.filter(
            status='Active',
            available_weight__gte=booking.weight,
            user__profile__kyc_status='APPROVED'
        ).exclude(
            user=booking.sender  # Never match with self
        )
        
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
            status__in=['Waiting Traveller', 'REQUEST_CREATED'],
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

class BookingWorkflowService:
    @staticmethod
    def trigger_websocket_notification(booking, event_type, message):
        def send_notification():
            try:
                channel_layer = get_channel_layer()
                if not channel_layer:
                    return
                    
                # Notify sender
                sender_group = f"user_{booking.sender.id}_notifications"
                async_to_sync(channel_layer.group_send)(
                    sender_group,
                    {
                        'type': 'booking_status_update',
                        'event_type': event_type,
                        'message': message,
                        'booking_id': booking.id,
                        'status': booking.status
                    }
                )
                
                # Notify traveler if assigned
                if booking.traveler:
                    traveler_group = f"user_{booking.traveler.id}_notifications"
                    async_to_sync(channel_layer.group_send)(
                        traveler_group,
                        {
                            'type': 'booking_status_update',
                            'event_type': event_type,
                            'message': message,
                            'booking_id': booking.id,
                            'status': booking.status
                        }
                    )
            except Exception as e:
                print(f"Websocket notification failed: {e}")
                
        transaction.on_commit(send_notification)

    @staticmethod
    def send_request(booking):
        if booking.status not in ['MATCH_FOUND', 'REQUEST_CREATED', 'Waiting Traveller', 'Draft']:
            raise ValueError(f"Cannot send request from status {booking.status}")
        
        booking.status = 'REQUEST_SENT'
        booking.save()
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'request_sent', f"Booking #{booking.id} request has been sent to traveler."
        )
        return booking

    @staticmethod
    def accept_request(booking):
        if booking.status != 'REQUEST_SENT':
            raise ValueError(f"Cannot accept request from status {booking.status}")
            
        booking.status = 'ACCEPTED'
        booking.save()
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'accepted', f"Traveler has accepted Booking #{booking.id}."
        )
        return booking

    @staticmethod
    def process_payment(booking):
        if booking.status != 'ACCEPTED':
            raise ValueError(f"Cannot process payment from status {booking.status}")
            
        booking.status = 'PAID'
        booking.payment_status = 'Escrow Hold'
        booking.escrow_status = 'Active Hold'
        booking.save()
        
        # Deduct from Sender's Available Balance and lock into Sender's Escrow Balance
        try:
            reward_amt = booking.reward or 0
            if reward_amt > 0 and booking.sender:
                sender_wallet, _ = Wallet.objects.get_or_create(user=booking.sender)
                # Deduct from available balance if sufficient, else direct lock
                if sender_wallet.balance_available >= reward_amt:
                    sender_wallet.balance_available -= reward_amt
                sender_wallet.balance_escrow += reward_amt
                sender_wallet.save()

                Transaction.objects.create(
                    wallet=sender_wallet,
                    amount=reward_amt,
                    type='Escrow Hold',
                    status='Completed',
                    description=f"₹{reward_amt} locked in Escrow for Booking #{booking.id} ({booking.package_name})"
                )
        except Exception as e:
            print(f"Failed to record sender escrow wallet hold: {e}")

        BookingWorkflowService.trigger_websocket_notification(
            booking, 'paid', f"Payment received for Booking #{booking.id}. Funds in escrow."
        )
        return booking

    @staticmethod
    def upload_verification(booking):
        if booking.status != 'PAID':
            raise ValueError(f"Cannot verify parcel from status {booking.status}")
            
        booking.status = 'PARCEL_VERIFIED'
        booking.save()
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'parcel_verified', f"Parcel for Booking #{booking.id} is verified."
        )
        return booking

    @staticmethod
    def update_transit_status(booking, new_status):
        valid_statuses = ['IN_TRANSIT', 'ARRIVED', 'OUT_FOR_DELIVERY']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid transit status: {new_status}")
            
        booking.status = new_status
        booking.save()
        
        message_map = {
            'IN_TRANSIT': 'Your parcel is now in transit.',
            'ARRIVED': 'Your parcel has arrived at the destination city.',
            'OUT_FOR_DELIVERY': 'Your parcel is out for delivery. OTP generated.'
        }
        
        BookingWorkflowService.trigger_websocket_notification(
            booking, new_status.lower(), message_map[new_status]
        )
        return booking

    @staticmethod
    def complete_delivery(booking, otp):
        if booking.status != 'OUT_FOR_DELIVERY':
            raise ValueError(f"Cannot complete delivery from status {booking.status}")
            
        if booking.delivery_otp != otp:
            raise ValueError("Invalid OTP")
            
        booking.status = 'DELIVERED'
        booking.save()
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'delivered', f"Booking #{booking.id} has been delivered successfully!"
        )

        # Immediately release escrow into Traveler's wallet and deduct from Sender's escrow vault
        try:
            booking = BookingWorkflowService.release_escrow(booking)
        except Exception as e:
            print(f"Auto escrow release error: {e}")

        return booking

    @staticmethod
    def release_escrow(booking):
        if booking.status not in ['DELIVERED', 'PAYMENT_RELEASED']:
            raise ValueError(f"Cannot release payment for non-delivered booking")
            
        reward_amt = booking.reward or 0

        # 1. Deduct Escrow from Sender Wallet
        try:
            if booking.sender and reward_amt > 0:
                sender_wallet, _ = Wallet.objects.get_or_create(user=booking.sender)
                if sender_wallet.balance_escrow >= reward_amt:
                    sender_wallet.balance_escrow -= reward_amt
                else:
                    sender_wallet.balance_escrow = 0
                sender_wallet.save()

                Transaction.objects.create(
                    wallet=sender_wallet,
                    amount=reward_amt,
                    type='Payment Sent',
                    status='Completed',
                    description=f"Escrow Released & Transferred to Traveler for Booking #{booking.id}"
                )
        except Exception as se:
            print(f"Error updating sender wallet escrow release: {se}")

        # 2. Credit Traveler Wallet Available Balance
        if booking.traveler and reward_amt > 0:
            traveler_wallet, _ = Wallet.objects.get_or_create(user=booking.traveler)
            traveler_wallet.balance_available += reward_amt
            traveler_wallet.save()
            
            Transaction.objects.create(
                wallet=traveler_wallet,
                amount=reward_amt,
                type='Payment Received',
                status='Completed',
                description=f"Payment received for Delivery of Booking #{booking.id} ({booking.package_name})"
            )
        
        booking.status = 'PAYMENT_RELEASED'
        booking.payment_status = 'Released'
        booking.escrow_status = 'Released'
        booking.save()
        
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'payment_released', f"Payment released to traveler for Booking #{booking.id}."
        )
        return booking
