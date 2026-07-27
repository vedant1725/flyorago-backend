from django.db import models
from django.conf import settings
import uuid

class TrustProfile(models.Model):
    LEVEL_CHOICES = (
        ('ELITE', 'Elite Trusted'),
        ('PLATINUM', 'Platinum'),
        ('GOLD', 'Gold'),
        ('SILVER', 'Silver'),
        ('STANDARD', 'Standard'),
        ('HIGH_RISK', 'High Risk'),
    )
    
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('FROZEN', 'Frozen'),
        ('BANNED', 'Banned'),
        ('REVIEW', 'Manual Review'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trust_profile')
    score = models.IntegerField(default=550)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='STANDARD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Advanced AI stats
    ai_confidence_score = models.IntegerField(default=50) # 0 to 100
    delivery_success_rate = models.FloatField(default=100.0) # Percentage
    cancellation_rate = models.FloatField(default=0.0) # Percentage
    fraud_risk_score = models.FloatField(default=0.0) # Percentage
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_level(self):
        if self.score >= 950:
            self.level = 'ELITE'
        elif self.score >= 850:
            self.level = 'PLATINUM'
        elif self.score >= 750:
            self.level = 'GOLD'
        elif self.score >= 650:
            self.level = 'SILVER'
        elif self.score >= 550:
            self.level = 'STANDARD'
        else:
            self.level = 'HIGH_RISK'

    def save(self, *args, **kwargs):
        # Ensure score stays between 0 and 1000
        self.score = max(0, min(1000, self.score))
        self.update_level()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.score} ({self.level})"

class TrustActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(TrustProfile, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=100)
    score_change = models.IntegerField()
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.profile.user.email}] {self.score_change:+d} - {self.activity_type}"

class RiskLog(models.Model):
    SEVERITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(TrustProfile, on_delete=models.CASCADE, related_name='risk_logs')
    risk_factor = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    ai_decision = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.severity}] {self.profile.user.email} - {self.risk_factor}"
