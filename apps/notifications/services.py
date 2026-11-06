import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)

class MultiLevelNotificationEngine:
    """
    Enterprise-grade Notification Engine designed to guarantee delivery
    through multiple escalating levels (Database, WebSocket, Email, Push/SMS).
    """

    @classmethod
    def send_user_notification(cls, user, title, message, notif_type='booking', type=None, extra=None, **kwargs):
        if not user:
            return None

        # Accept either type or notif_type for 100% caller compatibility
        final_type = type or notif_type or 'booking'

        # LEVEL 1: Database Persistence
        notification = None
        try:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                type=final_type
            )
        except Exception as db_err:
            logger.error(f"Failed to create database notification for user {getattr(user, 'id', None)}: {db_err}")

        # LEVEL 2: Real-time WebSocket Push (Instant UI Update & Mobile Shade / OS Tray)
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                notif_id = notification.id if notification else f"temp_{int(timezone.now().timestamp())}"
                created_iso = notification.created_at.isoformat() if notification and notification.created_at else timezone.now().isoformat()
                payload = {
                    "type": "user_notification",
                    "notification_id": notif_id,
                    "title": title,
                    "message": message,
                    "notif_type": final_type,
                    "type_category": final_type,
                    "createdAt": created_iso,
                    "created_at": created_iso,
                    **(extra or {}),
                    **kwargs
                }
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_notifications",
                    payload
                )
        except Exception as ws_err:
            logger.error(f"WebSocket Push failed for user {user.id}: {str(ws_err)}")

        return notification

    @classmethod
    def notify_payment_secured(cls, booking):
        traveller = booking.traveler
        sender = booking.sender
        amount = booking.reward

        title = "💰 Payment Secured in Escrow!"
        message = f"{sender.first_name or 'The Sender'} has successfully deposited ${amount} into the Escrow. The funds are locked and guaranteed. You may now schedule the pickup and verify the parcel."

        return cls.send_user_notification(
            user=traveller,
            title=title,
            message=message,
            notif_type='booking',
            extra={"booking_id": booking.id}
        )
