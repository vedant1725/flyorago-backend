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
        Calculates and updates user trust score dynamically from their real database activity
        and syncs live TrustActivityLog records explaining every score increase/decrease.
        """
        from django.db.models import Q
        profile, _ = TrustProfile.objects.get_or_create(user=user)
        if profile.status in ['FROZEN', 'BANNED']:
            return profile

        score = 500
        criteria_logs = []

        # 1. Base Score
        criteria_logs.append({
            'type': 'BASE_SCORE',
            'change': 500,
            'reason': 'Base Account Signup Trust Credit'
        })

        # 2. Email Verification
        if getattr(user, 'is_verified', False) or getattr(user, 'email', None):
            score += 15
            criteria_logs.append({
                'type': 'EMAIL_VERIFIED',
                'change': 15,
                'reason': 'Email Address Verified'
            })

        # 3. Phone Verification
        if getattr(user, 'phone_number', None):
            score += 25
            criteria_logs.append({
                'type': 'PHONE_VERIFIED',
                'change': 25,
                'reason': 'Mobile Number Verified'
            })

        # 4. KYC Government ID / Passport Approval Status
        user_profile = getattr(user, 'profile', None)
        if user_profile and getattr(user_profile, 'kyc_status', '') == 'APPROVED':
            score += 180
            criteria_logs.append({
                'type': 'KYC_APPROVED',
                'change': 180,
                'reason': 'KYC & Government ID/Passport Approved'
            })

        # 5. Successful Deliveries / Bookings
        completed_count = 0
        cancelled_count = 0
        try:
            from bookings.models import Booking
            completed_count = Booking.objects.filter(
                Q(sender=user) | Q(traveler=user),
                status__in=['DELIVERED', 'PAYMENT_RELEASED', 'RATED', 'Completed']
            ).count()
            if completed_count > 0:
                score += completed_count * 15
                criteria_logs.append({
                    'type': 'DELIVERY_SUCCESS',
                    'change': completed_count * 15,
                    'reason': f'{completed_count} Successful Deliveries Completed (+15 each)'
                })

            cancelled_count = Booking.objects.filter(
                Q(sender=user) | Q(traveler=user),
                status__in=['CANCELLED', 'REJECTED']
            ).count()
            if cancelled_count > 0:
                score -= cancelled_count * 20
                criteria_logs.append({
                    'type': 'BOOKING_CANCELLED',
                    'change': -cancelled_count * 20,
                    'reason': f'{cancelled_count} Booking Cancellation Penalty (-20 each)'
                })
        except Exception:
            pass

        # 6. Reviews Score
        try:
            from reviews.models import Review
            five_star_reviews = Review.objects.filter(reviewee=user, rating=5).count()
            if five_star_reviews > 0:
                score += five_star_reviews * 10
                criteria_logs.append({
                    'type': 'FIVE_STAR_REVIEW',
                    'change': five_star_reviews * 10,
                    'reason': f'{five_star_reviews} 5-Star Ratings Received (+10 each)'
                })
        except Exception:
            pass

        # 7. Manual Admin Overrides
        manual_logs = TrustActivityLog.objects.filter(profile=profile, activity_type='ADMIN_OVERRIDE')
        for l in manual_logs:
            score += l.score_change
            criteria_logs.append({
                'type': 'ADMIN_OVERRIDE',
                'change': l.score_change,
                'reason': l.reason or 'Admin Score Adjustment'
            })

        # Update stats
        total_bks = completed_count + cancelled_count
        profile.delivery_success_rate = round((completed_count / total_bks * 100.0), 1) if total_bks > 0 else 100.0
        profile.cancellation_rate = round((cancelled_count / total_bks * 100.0), 1) if total_bks > 0 else 0.0
        profile.ai_confidence_score = 95 if (user_profile and getattr(user_profile, 'kyc_status', '') == 'APPROVED') else (75 if getattr(user, 'phone_number', None) else 50)
        profile.fraud_risk_score = 0.0 if score >= 600 else round(min(100.0, (600 - score) * 0.2), 1)

        # Clamp score between 0 and 1000
        profile.score = max(0, min(1000, score))
        profile.save()

        # Sync live TrustActivityLog table so frontend timeline displays live active items
        auto_types = ['BASE_SCORE', 'EMAIL_VERIFIED', 'PHONE_VERIFIED', 'KYC_APPROVED', 'DELIVERY_SUCCESS', 'BOOKING_CANCELLED', 'FIVE_STAR_REVIEW']
        TrustActivityLog.objects.filter(profile=profile, activity_type__in=auto_types).delete()

        for log_item in criteria_logs:
            if log_item['type'] in auto_types:
                TrustActivityLog.objects.create(
                    profile=profile,
                    activity_type=log_item['type'],
                    score_change=log_item['change'],
                    reason=log_item['reason']
                )

        return profile
