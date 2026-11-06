from notifications.services import MultiLevelNotificationEngine
from notifications.models import Notification
from notifications.services import MultiLevelNotificationEngine
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
        acceptable_statuses = ['REQUEST_SENT', 'REQUEST_CREATED', 'REQUEST_RECEIVED', 'Waiting Traveller', 'Booking Requested', 'PENDING']
        if booking.status not in acceptable_statuses:
            raise ValueError(f"Cannot accept request from status {booking.status}")
            
        booking.status = 'ACCEPTED'
        booking.save()
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'accepted', f"Traveler has accepted Booking #{booking.id}."
        )
        return booking

    @staticmethod
    def process_payment(booking, payment_method='card'):
        if booking.status != 'ACCEPTED':
            raise ValueError(f"Cannot process payment from status {booking.status}")
            
        from payments.models import SystemSetting, PaymentRecord
        from wallet.models import Wallet, Transaction
        from decimal import Decimal
        import random

        fee_str = SystemSetting.get_setting("platform_fee", "10.00")
        platform_fee = Decimal(fee_str)
        total_amount = booking.reward + platform_fee

        sender_wallet, _ = Wallet.objects.get_or_create(user=booking.sender)

        method_clean = (payment_method or 'card').lower().strip()
        
        # 1. If paying with Wallet: Check if balance is sufficient
        if method_clean == 'wallet':
            if sender_wallet.balance_available < total_amount:
                raise ValueError(
                    f"Insufficient wallet balance! Total required is ₹{total_amount:.2f}, but your available balance is ₹{sender_wallet.balance_available:.2f}. Please add money to wallet or use Card/UPI payment."
                )
            # Deduct from available balance
            sender_wallet.balance_available -= total_amount
            
            # Record wallet debit transaction
            Transaction.objects.create(
                wallet=sender_wallet,
                amount=total_amount,
                type='Payment Sent',
                status='Completed',
                description=f"Payment for Booking #{booking.id} deducted from wallet balance",
                reference_id=str(booking.id)
            )

        # 2. Add to Escrow balance (Safely locked in Escrow)
        sender_wallet.balance_escrow += total_amount
        sender_wallet.save()

        # Update booking status
        booking.status = 'PAID'
        booking.payment_status = 'Escrow Hold'
        booking.escrow_status = 'Active Hold'
        booking.save()

        # Record Payment & Escrow transactions
        try:
            tx_id = f"ch_{random.randint(10000000, 99999999)}"
            PaymentRecord.objects.create(
                user=booking.sender,
                booking=booking,
                transaction_id=tx_id,
                amount=total_amount,
                platform_fee=platform_fee,
                status='Success'
            )

            Transaction.objects.create(
                wallet=sender_wallet,
                amount=total_amount,
                type='Escrow Hold',
                status='Completed',
                description=f"₹{total_amount:.2f} locked in Escrow for Booking #{booking.id} ({payment_method.upper()})",
                reference_id=str(booking.id)
            )
        except Exception as e:
            print(f"Failed to record platform fee or update wallet escrow: {e}")
        
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'paid', f"Payment received for Booking #{booking.id}. Funds in escrow."
        )
        return booking

    @staticmethod
    def upload_verification(booking):
        if booking.status not in ['PAID', 'ACCEPTED']:
            raise ValueError(f"Cannot verify parcel from status {booking.status}")
            
        booking.status = 'PARCEL_VERIFIED'
        booking.save()

        try:
            if hasattr(booking, 'shipment') and booking.shipment:
                from shipments.models import ShipmentLog
                ShipmentLog.objects.create(
                    shipment=booking.shipment,
                    status='Package Verified',
                    location=booking.trip.from_location if booking.trip else 'Pickup',
                    description="Parcel inspected and verified by traveler. Photos and weight confirmed."
                )
                MultiLevelNotificationEngine.send_user_notification(
                user=booking.sender,
                title='Parcel Verified & Picked Up! 📦',
                message=f'Traveler has verified and picked up your parcel "{booking.package_name}".',
                type='booking'
            )
        except Exception as e:
            print(f"Verification log note: {e}")

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

        try:
            if hasattr(booking, 'shipment') and booking.shipment:
                from shipments.models import ShipmentLog
                if new_status == 'IN_TRANSIT':
                    booking.shipment.status = 'In Transit'
                    booking.shipment.save()
                    ShipmentLog.objects.create(
                        shipment=booking.shipment,
                        status='In Transit',
                        location=booking.trip.from_location if booking.trip else 'Transit',
                        description="Traveler has started the journey with the parcel."
                    )
                elif new_status == 'ARRIVED':
                    booking.shipment.status = 'Out for Handoff'
                    booking.shipment.save()
                    ShipmentLog.objects.create(
                        shipment=booking.shipment,
                        status='Arrived',
                        location=booking.trip.to_location if booking.trip else 'Destination',
                        description="Traveler has arrived at the destination. Ready for QR verification handoff."
                    )
        except Exception as e:
            print(f"Shipment transit log note: {e}")
        
        message_map = {
            'IN_TRANSIT': 'Your parcel is now in transit.',
            'ARRIVED': 'Your parcel has arrived at the destination city.',
            'OUT_FOR_DELIVERY': 'Your parcel is out for delivery. QR verification code active.'
        }
        
        BookingWorkflowService.trigger_websocket_notification(
            booking, new_status.lower(), message_map[new_status]
        )
        return booking

    @staticmethod
    def complete_delivery(booking, otp):
        if booking.status not in ['OUT_FOR_DELIVERY', 'ARRIVED', 'IN_TRANSIT']:
            raise ValueError(f"Cannot complete delivery from status {booking.status}")
            
        if booking.delivery_otp and str(booking.delivery_otp).strip() != str(otp).strip():
            raise ValueError("Invalid verification OTP or QR token")
            
        booking.status = 'DELIVERED'
        booking.save()

        # Update associated shipment and log
        try:
            if hasattr(booking, 'shipment') and booking.shipment:
                booking.shipment.status = 'Delivered'
                booking.shipment.save()
                from shipments.models import ShipmentLog
                ShipmentLog.objects.create(
                    shipment=booking.shipment,
                    status='Delivered',
                    location=booking.trip.to_location if booking.trip else 'Destination',
                    description="Delivery confirmed via secure QR Code scan. Parcel successfully handed over."
                )
        except Exception as e:
            print(f"Shipment log update note: {e}")

        # Auto-release escrow to traveler wallet
        try:
            if booking.escrow_status == 'Active Hold':
                BookingWorkflowService.release_escrow(booking)
        except Exception as e:
            print(f"Auto escrow release note: {e}")

        # Send Notifications to both Sender and Traveler
        try:
            MultiLevelNotificationEngine.send_user_notification(
                user=booking.sender,
                title='Delivery Completed! 🎊',
                message=f'Your parcel "{booking.package_name}" has been successfully delivered and verified via QR verification.',
                type='booking'
            )
            MultiLevelNotificationEngine.send_user_notification(
                user=booking.traveler,
                title='Trip Success! 💰',
                message=f'Delivery verified! Reward of ₹{booking.reward} has been credited to your wallet.',
                type='booking'
            )
        except Exception as notif_err:
            print(f"Delivery notification note: {notif_err}")

        BookingWorkflowService.trigger_websocket_notification(
            booking, 'delivered', f"Booking #{booking.id} has been delivered successfully!"
        )
        return booking

    @staticmethod
    def release_escrow(booking):
        if booking.status != 'DELIVERED':
            raise ValueError(f"Cannot release payment for non-delivered booking")
            
        if booking.escrow_status != 'Active Hold':
            raise ValueError("No active escrow hold")
            
        from wallet.models import Wallet as WModel, Transaction as TxModel
        from payments.models import SystemSetting, PaymentRecord
        from decimal import Decimal

        fee_str = SystemSetting.get_setting("platform_fee", "10.00")
        platform_fee = Decimal(fee_str)
        total_escrow_hold = booking.reward + platform_fee

        # 1. Deduct escrow balance from sender & log Escrow Release Debit for sender
        try:
            sender_w = WModel.objects.filter(user=booking.sender).first()
            if sender_w:
                if sender_w.balance_escrow >= total_escrow_hold:
                    sender_w.balance_escrow -= total_escrow_hold
                else:
                    sender_w.balance_escrow = Decimal('0.00')
                sender_w.save()

                # Record transaction for sender showing reward paid to traveler
                traveler_name = f"{booking.traveler.first_name} {booking.traveler.last_name}".strip() if booking.traveler else "Traveler"
                if not traveler_name and booking.traveler:
                    traveler_name = booking.traveler.email.split('@')[0]
                TxModel.objects.create(
                    wallet=sender_w,
                    amount=booking.reward,
                    type='Payment Sent',
                    status='Completed',
                    description=f"Escrow Released & Transferred to Traveler ({traveler_name}) for Booking #{booking.id}",
                    reference_id=str(booking.id)
                )

                # Record transaction for sender showing platform fee charge
                if platform_fee > Decimal('0.00'):
                    TxModel.objects.create(
                        wallet=sender_w,
                        amount=platform_fee,
                        type='Payment Sent',
                        status='Completed',
                        description=f"Platform Service Fee charged for Booking #{booking.id}",
                        reference_id=f"FEE-S-{booking.id}"
                    )
        except Exception as esc_err:
            print("Escrow deduct note:", esc_err)

        # 2. Release Net Reward to Traveler (Reward minus Traveler Platform Fee)
        # Calculate traveler platform fee (capped so traveler net earning is never negative)
        traveler_fee = min(platform_fee, booking.reward)
        net_traveler_amount = max(Decimal('0.00'), booking.reward - traveler_fee)

        wallet, _ = Wallet.objects.get_or_create(user=booking.traveler)
        wallet.balance_available += net_traveler_amount
        wallet.save()
        
        sender_name = f"{booking.sender.first_name} {booking.sender.last_name}".strip() if booking.sender else "Sender"
        if not sender_name and booking.sender:
            sender_name = booking.sender.email.split('@')[0]

        # Record Gross Reward Credit for Traveler
        Transaction.objects.create(
            wallet=wallet,
            amount=booking.reward,
            type='Escrow Release',
            status='Completed',
            description=f"Gross Reward received from Sender ({sender_name}) for Booking #{booking.id}",
            reference_id=str(booking.id)
        )

        # Record Platform Fee deduction from Traveler
        if traveler_fee > Decimal('0.00'):
            Transaction.objects.create(
                wallet=wallet,
                amount=traveler_fee,
                type='Withdrawal',
                status='Completed',
                description=f"Platform Service Fee deducted from reward for Booking #{booking.id}",
                reference_id=f"FEE-T-{booking.id}"
            )

        # Record Platform Fee collected from traveler in PaymentRecord for Admin accounting
        try:
            PaymentRecord.objects.create(
                user=booking.traveler,
                booking=booking,
                transaction_id=f"fee_trv_{booking.id}_{random.randint(1000, 9999)}",
                amount=traveler_fee,
                platform_fee=traveler_fee,
                status='Success'
            )
        except Exception as pr_err:
            print(f"PaymentRecord traveler fee note: {pr_err}")
        
        booking.status = 'PAYMENT_RELEASED'
        booking.payment_status = 'Released'
        booking.escrow_status = 'Released'
        booking.save()
        
        BookingWorkflowService.trigger_websocket_notification(
            booking, 'payment_released', f"Payment released to traveler for Booking #{booking.id} (Net: ₹{net_traveler_amount:.2f})."
        )
        return booking
