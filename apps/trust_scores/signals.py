from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import TrustProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_trust_profile_on_signup(sender, instance, created, **kwargs):
    """Create a trust profile for every new user automatically."""
    if created:
        TrustProfile.objects.create(user=instance)


def award_trust(user, activity_key, custom_reason=None):
    """
    Safe helper to award trust points.
    Can be imported and called from any app without circular imports.
    """
    from .engine import TrustEngine
    TrustEngine.adjust_score(user, activity_key, custom_reason)


# ─── Booking Signals ───────────────────────────────────────────────────────────
def connect_booking_signals():
    try:
        from bookings.models import Booking

        @receiver(post_save, sender=Booking)
        def on_booking_status_change(sender, instance, created, **kwargs):
            if created:
                return
            
            try:
                old = Booking.objects.filter(pk=instance.pk).first()
                status = instance.status

                if status == 'DELIVERED':
                    if instance.traveler:
                        award_trust(instance.traveler, 'SUCCESSFUL_DELIVERY', 'Successful Parcel Delivery')
                    if instance.sender:
                        award_trust(instance.sender, 'SUCCESSFUL_DELIVERY', 'Parcel Delivered Successfully')

                elif status == 'PARCEL_VERIFIED':
                    if instance.sender:
                        award_trust(instance.sender, 'PARCEL_VERIFIED', 'Parcel Verified Before Sending')

                elif status == 'CANCELLED':
                    # Penalize the user who cancelled 
                    if instance.traveler:
                        award_trust(instance.traveler, 'USER_CANCELLATION', 'Booking Cancelled by Traveler')
                    
                elif status == 'REJECTED':
                    if instance.sender:
                        award_trust(instance.sender, 'PARCEL_REJECTED', 'Parcel Rejected')

            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Trust signal error (booking): {e}")

    except ImportError:
        pass


# ─── Review Signals ────────────────────────────────────────────────────────────
def connect_review_signals():
    try:
        from reviews.models import Review

        @receiver(post_save, sender=Review)
        def on_review_created(sender, instance, created, **kwargs):
            if not created:
                return
            try:
                reviewed_user = instance.reviewed_user
                rating = instance.rating

                if rating == 5:
                    award_trust(reviewed_user, 'FIVE_STAR_REVIEW', '5-Star Review Received')
                elif rating == 4:
                    from .engine import TrustEngine
                    from .models import TrustProfile, TrustActivityLog
                    profile, _ = TrustProfile.objects.get_or_create(user=reviewed_user)
                    if profile.status not in ['FROZEN', 'BANNED']:
                        profile.score = min(1000, profile.score + 5)
                        profile.save()
                        TrustActivityLog.objects.create(
                            profile=profile, activity_type='POSITIVE_REVIEW',
                            score_change=5, reason='4-Star Review Received'
                        )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Trust signal error (review): {e}")

    except ImportError:
        pass


# ─── KYC Signals ──────────────────────────────────────────────────────────────
def connect_kyc_signals():
    try:
        from users.models import User

        @receiver(post_save, sender=User)
        def on_user_verified(sender, instance, created, **kwargs):
            if created:
                return
            try:
                if instance.is_verified and instance.phone_number:
                    award_trust(instance, 'PHONE_VERIFIED', 'Phone Number Verified')
                if instance.email and instance.is_verified:
                    award_trust(instance, 'EMAIL_VERIFIED', 'Email Address Verified')
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Trust signal error (kyc): {e}")

    except ImportError:
        pass


# ─── Connect All Signals ──────────────────────────────────────────────────────
connect_booking_signals()
connect_review_signals()
connect_kyc_signals()
