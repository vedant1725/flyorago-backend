from .models import TrustProfile, TrustActivityLog, RiskLog

class TrustEngine:
    """
    Simulated AI Engine for dynamic trust scoring.
    """
    
    SCORE_WEIGHTS = {
        'SUCCESSFUL_DELIVERY': 15,
        'FIVE_STAR_REVIEW': 8,
        'REPEAT_DELIVERY': 5,
        'VERIFIED_PASSPORT': 80,
        'GOVERNMENT_ID': 50,
        'FACE_VERIFICATION': 50,
        'PHONE_VERIFIED': 20,
        'EMAIL_VERIFIED': 10,
        'PROFILE_COMPLETE': 15,
        'PARCEL_VERIFIED': 20,
        'FAST_RESPONSE': 10,
        'ON_TIME_DELIVERY': 20,
        'NO_VIOLATIONS_30D': 25,
        
        # Penalties
        'USER_CANCELLATION': -20,
        'LATE_ARRIVAL': -15,
        'PARCEL_REJECTED': -25,
        'FAKE_PROFILE': -200,
        'FRAUD_DETECTION': -500,
    }

    @staticmethod
    def adjust_score(user, activity_key, custom_reason=None):
        """
        Adjusts user trust score based on a predefined activity key.
        """
        if activity_key not in TrustEngine.SCORE_WEIGHTS:
            return None
            
        profile, created = TrustProfile.objects.get_or_create(user=user)
        
        if profile.status in ['FROZEN', 'BANNED']:
            return profile # Do not update if frozen or banned

        score_change = TrustEngine.SCORE_WEIGHTS[activity_key]
        reason = custom_reason or activity_key.replace('_', ' ').title()

        profile.score += score_change
        profile.save()

        # Log Activity
        TrustActivityLog.objects.create(
            profile=profile,
            activity_type=activity_key,
            score_change=score_change,
            reason=reason
        )
        
        # Simulated AI logic for risk flags
        if score_change < 0 and profile.score < 550:
            profile.ai_confidence_score = max(0, profile.ai_confidence_score - 10)
            profile.fraud_risk_score = min(100, profile.fraud_risk_score + 15)
            profile.save()
            
            if profile.fraud_risk_score >= 80:
                RiskLog.objects.create(
                    profile=profile,
                    risk_factor="High negative activity pattern detected",
                    severity="HIGH",
                    ai_decision="Flagged for manual review."
                )
                profile.status = 'REVIEW'
                profile.save()

        return profile

    @staticmethod
    def log_risk(user, risk_factor, severity, ai_decision):
        profile, _ = TrustProfile.objects.get_or_create(user=user)
        RiskLog.objects.create(
            profile=profile,
            risk_factor=risk_factor,
            severity=severity,
            ai_decision=ai_decision
        )
        if severity == 'CRITICAL':
            profile.status = 'FROZEN'
            profile.save()

    @staticmethod
    def recalculate_profile(user):
        """
        Calculates and updates user trust score dynamically from their real database activity.
        """
        from django.db.models import Q
        profile, _ = TrustProfile.objects.get_or_create(user=user)
        if profile.status in ['FROZEN', 'BANNED']:
            return profile

        score = 500

        # 1. Verification Bonuses
        if getattr(user, 'is_verified', False):
            score += 15
        if getattr(user, 'phone_number', None):
            score += 25

        # 2. KYC Approval Status
        user_profile = getattr(user, 'profile', None)
        if user_profile and getattr(user_profile, 'kyc_status', '') == 'APPROVED':
            score += 180

        # 3. Successful Deliveries / Bookings
        try:
            from bookings.models import Booking
            completed_count = Booking.objects.filter(
                Q(sender=user) | Q(traveler=user),
                status__in=['DELIVERED', 'PAYMENT_RELEASED', 'RATED']
            ).count()
            score += completed_count * 15

            cancelled_count = Booking.objects.filter(
                Q(sender=user) | Q(traveler=user),
                status='CANCELLED'
            ).count()
            score -= cancelled_count * 20
        except Exception:
            pass

        # 4. Activity log adjustments (manual admin overrides)
        manual_logs = TrustActivityLog.objects.filter(profile=profile, activity_type='ADMIN_OVERRIDE')
        for l in manual_logs:
            score += l.score_change

        # Clamp score between 0 and 1000
        profile.score = max(0, min(1000, score))
        profile.save()
        return profile
