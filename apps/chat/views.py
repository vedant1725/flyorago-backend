from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from common.responses import success_response, failure_response
from bookings.models import Booking

User = get_user_model()

# Valid active journey statuses where communication between Sender & Traveler is permitted
# Communication is strictly blocked before acceptance (REQUEST_SENT, PENDING) and after delivery confirmed (DELIVERED, COMPLETED, PAYMENT_RELEASED)
ACTIVE_CHAT_STATUSES = [
    'ACCEPTED',
    'Traveller Accepted',
    'PAID',
    'Payment Completed',
    'PARCEL_VERIFIED',
    'Parcel Verification',
    'IN_TRANSIT',
    'In Transit',
    'ARRIVED',
    'Flight Landed',
    'OUT_FOR_DELIVERY',
    'Out For Delivery',
    'OTP_GENERATED',
]

def check_chat_permission(user_a, user_b):
    """
    Checks if messaging is allowed between two users.
    Condition:
    1. Inspect the latest booking between user_a and user_b.
    2. If the latest booking is DELIVERED, COMPLETED, or PAYMENT_RELEASED -> Strictly lock/close messaging!
    3. If the latest booking is in ACTIVE_CHAT_STATUSES (ACCEPTED, PAID, PARCEL_VERIFIED, IN_TRANSIT, OUT_FOR_DELIVERY) -> Allow chat.
    4. Otherwise (unaccepted or no booking) -> Disallow chat.
    """
    latest_booking = Booking.objects.filter(
        (Q(sender=user_a, traveler=user_b) | Q(sender=user_b, traveler=user_a))
    ).order_by('-id').first()

    if not latest_booking:
        return False, None, "You can only message a user who has an accepted trip delivery with you."

    # Rule 1: Delivery confirmed / completed -> STRICTLY CLOSE CHAT
    if latest_booking.status in ['DELIVERED', 'Delivered', 'COMPLETED', 'Completed', 'PAYMENT_RELEASED']:
        return False, latest_booking, "Delivery has been confirmed and completed. Messaging is closed."

    # Rule 2: Active accepted journey -> ALLOW CHAT
    if latest_booking.status in ACTIVE_CHAT_STATUSES:
        return True, latest_booking, None

    # Rule 3: Not yet accepted
    if latest_booking.status in ['REQUEST_CREATED', 'REQUEST_SENT', 'REQUEST_RECEIVED', 'PENDING', 'Booking Requested', 'Waiting Traveller']:
        return False, latest_booking, "Messaging is available only after the traveler accepts the trip request."

    return False, latest_booking, "Messaging is not available for this booking status."


class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = []
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = self.request.user

        # 1. Auto-discover accepted bookings where user is sender or traveler
        active_bookings = Booking.objects.filter(
            (Q(sender=user) | Q(traveler=user)),
            status__in=ACTIVE_CHAT_STATUSES
        ).select_related('sender', 'traveler')

        for b in active_bookings:
            partner = b.traveler if b.sender_id == user.id else b.sender
            if partner and partner.id != user.id:
                # Ensure conversation object exists in database
                existing = Conversation.objects.filter(participants=user).filter(participants=partner).first()
                if not existing:
                    new_conv = Conversation.objects.create()
                    new_conv.participants.add(user, partner)
                    new_conv.save()
                    # Add friendly system starter message
                    starter_role = "Traveler" if b.traveler_id == user.id else "Sender"
                    package_name = b.package_name or "Parcel"
                    Message.objects.create(
                        conversation=new_conv,
                        sender=partner,
                        text=f"Hello! Trip request for '{package_name}' has been accepted. You can now coordinate handover location and timing here."
                    )

        # 2. Return all conversations where user is a participant
        return Conversation.objects.filter(participants=user).prefetch_related('participants', 'messages').order_by('-updated_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return success_response(data=serializer.data, message="Conversations list retrieved")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        participant_id = request.data.get('participant_id')
        if not participant_id:
            return failure_response(message="participant_id is required")
        
        other_user = get_object_or_404(User, id=participant_id)
        if other_user == request.user:
            return failure_response(message="You cannot start a conversation with yourself")

        # Verify MNC Company Standard permission rule: Traveler must have accepted request, and delivery not yet confirmed
        can_chat, booking_obj, err_msg = check_chat_permission(request.user, other_user)
        if not can_chat:
            return failure_response(message=err_msg or "Messaging is not allowed for this booking status.", status_code=status.HTTP_403_FORBIDDEN)

        # Check for existing chat
        existing = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
        if existing:
            serializer = self.get_serializer(existing, context={'request': request})
            return success_response(data=serializer.data, message="Conversation already exists")

        # Create new chat
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other_user)
        conv.save()

        # Create welcome message
        package_name = booking_obj.package_name if booking_obj else "Parcel"
        Message.objects.create(
            conversation=conv,
            sender=other_user,
            text=f"Hello! Trip request for '{package_name}' is accepted. We can now coordinate directly."
        )

        serializer = self.get_serializer(conv, context={'request': request})
        return success_response(data=serializer.data, message="Conversation created successfully", status_code=status.HTTP_201_CREATED)


class MessageListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = []
    serializer_class = MessageSerializer

    def get_queryset(self):
        conv_id = self.kwargs['conversation_id']
        conv = get_object_or_404(Conversation, id=conv_id, participants=self.request.user)
        
        # Mark all messages sent by the other participant as seen on fetch
        conv.messages.exclude(sender=self.request.user).update(is_seen=True)
        return conv.messages.all().order_by('created_at')

    def list(self, request, *args, **kwargs):
        conv_id = self.kwargs['conversation_id']
        conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
        
        # Also retrieve active booking info to inform mobile app of chat validity
        other_participant = conv.participants.exclude(id=request.user.id).first()
        can_chat = True
        booking_info = None
        if other_participant:
            is_allowed, b_obj, _ = check_chat_permission(request.user, other_participant)
            can_chat = is_allowed
            if b_obj:
                booking_info = {
                    'booking_id': b_obj.id,
                    'package_name': b_obj.package_name,
                    'status': b_obj.status,
                    'reward': str(b_obj.reward),
                    'from_location': getattr(b_obj.trip, 'from_location', '') if b_obj.trip else '',
                    'to_location': getattr(b_obj.trip, 'to_location', '') if b_obj.trip else '',
                }

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data={
            'messages': serializer.data,
            'can_chat': can_chat,
            'booking_info': booking_info,
        }, message="Messages fetched")

    def create(self, request, *args, **kwargs):
        conv_id = self.kwargs['conversation_id']
        conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
        
        other_participant = conv.participants.exclude(id=request.user.id).first()
        if not other_participant:
            return failure_response(message="Invalid conversation participant.")

        # Enforce rule: only accepted requests, and no messages after delivery confirmed!
        can_chat, _, err_msg = check_chat_permission(request.user, other_participant)
        if not can_chat:
            return failure_response(
                message=err_msg or "Cannot send message: Delivery has been completed or request is not active.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            msg = serializer.save(
                conversation=conv,
                sender=request.user
            )
            # Update conversation timestamp
            conv.save()
            return success_response(data=serializer.data, message="Message sent", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to send message")
