import logging
from django.utils import timezone
from notifications.models import EmailLog

from .client import ResendEmailClient
from .templates import (
    build_account_restricted_email,
    build_account_reactivated_email,
    build_welcome_email,
    build_verification_otp_email,
    build_password_reset_otp_email,
    build_kyc_status_email,
    build_generic_event_email
)

logger = logging.getLogger(__name__)

class EmailService:
    """
    Central Non-Blocking Production Email Service for FlyoraGo.
    Guarantees that email failures never interrupt calling business operations.
    """

    @classmethod
    def _dispatch_email(cls, recipient: str, subject: str, html_content: str, text_content: str, event_name: str, template_name: str, idempotency_key: str = None) -> bool:
        """
        Internal safe dispatch wrapper handling idempotency, logging, and Resend HTTP delivery.
        """
        if not recipient:
            logger.warning(f"Skipping email dispatch for event '{event_name}' — no recipient email provided.")
            return False

        # 1. Check Idempotency Key
        if idempotency_key:
            existing_log = EmailLog.objects.filter(idempotency_key=idempotency_key, status='SENT').first()
            if existing_log:
                logger.info(f"Duplicate email event suppressed via idempotency key: '{idempotency_key}'")
                return True

        # 2. Create EmailLog in QUEUED status
        log_entry = None
        try:
            log_entry = EmailLog.objects.create(
                recipient=recipient,
                template=template_name,
                subject=subject,
                event=event_name,
                provider='Resend',
                status='QUEUED',
                idempotency_key=idempotency_key
            )
        except Exception as db_err:
            logger.error(f"Failed to create EmailLog entry: {db_err}")

        # 3. Attempt Resend Delivery
        try:
            if log_entry:
                log_entry.status = 'SENDING'
                log_entry.save(update_fields=['status'])

            success, msg_id, err_detail = ResendEmailClient.send_email(
                recipient=recipient,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            if success:
                if log_entry:
                    log_entry.status = 'SENT'
                    log_entry.message_id = msg_id
                    log_entry.sent_at = timezone.now()
                    log_entry.save(update_fields=['status', 'message_id', 'sent_at'])
                return True
            else:
                if log_entry:
                    log_entry.status = 'FAILED'
                    log_entry.error = err_detail
                    log_entry.save(update_fields=['status', 'error'])
                logger.error(f"Resend dispatch failed for {recipient}: {err_detail}")
                return False

        except Exception as exc:
            logger.error(f"Unhandled exception during email dispatch to {recipient}: {str(exc)}")
            if log_entry:
                try:
                    log_entry.status = 'FAILED'
                    log_entry.error = str(exc)
                    log_entry.save(update_fields=['status', 'error'])
                except Exception:
                    pass
            return False


    # ─── HIGH-LEVEL EVENT TRIGGER METHODS ────────────────────────────────────

    @classmethod
    def send_account_restricted(cls, user, reason: str = None, event_id: str = None) -> bool:
        try:
            email = getattr(user, 'email', str(user))
            first_name = getattr(user, 'first_name', '') or email.split('@')[0]
            reason_clean = reason or "Account temporarily restricted by system administration."
            ikey = f"account-restricted:{getattr(user, 'id', user)}:{event_id or timezone.now().strftime('%Y%m%d%H%M%S')}"

            subject, html, text = build_account_restricted_email({'firstName': first_name, 'blockReason': reason_clean})
            return cls._dispatch_email(
                recipient=email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='ACCOUNT_RESTRICTED',
                template_name='account_restricted',
                idempotency_key=ikey
            )
        except Exception as e:
            logger.error(f"Error triggering send_account_restricted: {e}")
            return False

    @classmethod
    def send_account_reactivated(cls, user, event_id: str = None) -> bool:
        try:
            email = getattr(user, 'email', str(user))
            first_name = getattr(user, 'first_name', '') or email.split('@')[0]
            ikey = f"account-reactivated:{getattr(user, 'id', user)}:{event_id or timezone.now().strftime('%Y%m%d%H%M%S')}"

            subject, html, text = build_account_reactivated_email({'firstName': first_name})
            return cls._dispatch_email(
                recipient=email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='ACCOUNT_REACTIVATED',
                template_name='account_reactivated',
                idempotency_key=ikey
            )
        except Exception as e:
            logger.error(f"Error triggering send_account_reactivated: {e}")
            return False

    @classmethod
    def send_welcome(cls, user) -> bool:
        try:
            email = getattr(user, 'email', str(user))
            first_name = getattr(user, 'first_name', '') or email.split('@')[0]
            ikey = f"welcome:{getattr(user, 'id', user)}"

            subject, html, text = build_welcome_email({'firstName': first_name})
            return cls._dispatch_email(
                recipient=email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='WELCOME',
                template_name='welcome',
                idempotency_key=ikey
            )
        except Exception as e:
            logger.error(f"Error triggering send_welcome: {e}")
            return False

    @classmethod
    def send_verification_otp(cls, user, otp_code: str) -> bool:
        try:
            email = getattr(user, 'email', str(user))
            first_name = getattr(user, 'first_name', '') or email.split('@')[0]
            ikey = f"verify-otp:{getattr(user, 'id', user)}:{otp_code}"

            subject, html, text = build_verification_otp_email({'firstName': first_name, 'otp': otp_code})
            return cls._dispatch_email(
                recipient=email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='EMAIL_VERIFICATION_OTP',
                template_name='verification_otp',
                idempotency_key=ikey
            )
        except Exception as e:
            logger.error(f"Error triggering send_verification_otp: {e}")
            return False

    @classmethod
    def send_password_reset_otp(cls, user, otp_code: str) -> bool:
        try:
            email = getattr(user, 'email', str(user))
            first_name = getattr(user, 'first_name', '') or email.split('@')[0]
            ikey = f"reset-otp:{getattr(user, 'id', user)}:{otp_code}"

            subject, html, text = build_password_reset_otp_email({'firstName': first_name, 'otp': otp_code})
            return cls._dispatch_email(
                recipient=email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='PASSWORD_RESET_OTP',
                template_name='password_reset_otp',
                idempotency_key=ikey
            )
        except Exception as e:
            logger.error(f"Error triggering send_password_reset_otp: {e}")
            return False

    @classmethod
    def send_kyc_status_update(cls, user, status: str, rejection_reason: str = None) -> bool:
        try:
            email = getattr(user, 'email', str(user))
            first_name = getattr(user, 'first_name', '') or email.split('@')[0]
            ikey = f"kyc-update:{getattr(user, 'id', user)}:{status}:{timezone.now().strftime('%Y%m%d%H%M')}"

            subject, html, text = build_kyc_status_email({
                'firstName': first_name,
                'status': status,
                'rejectionReason': rejection_reason
            })
            return cls._dispatch_email(
                recipient=email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name=f'KYC_{status.upper()}',
                template_name='kyc_status',
                idempotency_key=ikey
            )
        except Exception as e:
            logger.error(f"Error triggering send_kyc_status_update: {e}")
            return False

    @classmethod
    def send_booking_notification(cls, recipient_email: str, recipient_name: str, title: str, message: str, details: list = None, badge: str = "BOOKING") -> bool:
        try:
            subject, html, text = build_generic_event_email(
                title=title,
                recipient_name=recipient_name,
                message=message,
                details=details,
                badge=badge,
                badge_type="info"
            )
            return cls._dispatch_email(
                recipient=recipient_email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='BOOKING_UPDATE',
                template_name='booking_notice'
            )
        except Exception as e:
            logger.error(f"Error triggering send_booking_notification: {e}")
            return False

    @classmethod
    def send_shipment_notification(cls, recipient_email: str, recipient_name: str, title: str, message: str, details: list = None, badge: str = "SHIPMENT") -> bool:
        try:
            subject, html, text = build_generic_event_email(
                title=title,
                recipient_name=recipient_name,
                message=message,
                details=details,
                badge=badge,
                badge_type="info"
            )
            return cls._dispatch_email(
                recipient=recipient_email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='SHIPMENT_UPDATE',
                template_name='shipment_notice'
            )
        except Exception as e:
            logger.error(f"Error triggering send_shipment_notification: {e}")
            return False

    @classmethod
    def send_payment_notification(cls, recipient_email: str, recipient_name: str, title: str, message: str, details: list = None, badge: str = "PAYMENT") -> bool:
        try:
            subject, html, text = build_generic_event_email(
                title=title,
                recipient_name=recipient_name,
                message=message,
                details=details,
                badge=badge,
                badge_type="success"
            )
            return cls._dispatch_email(
                recipient=recipient_email,
                subject=subject,
                html_content=html,
                text_content=text,
                event_name='PAYMENT_UPDATE',
                template_name='payment_notice'
            )
        except Exception as e:
            logger.error(f"Error triggering send_payment_notification: {e}")
            return False
