from django.contrib import admin
from .models import TrustProfile, TrustActivityLog, RiskLog

@admin.register(TrustProfile)
class TrustProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'level', 'status', 'fraud_risk_score')
    list_filter = ('level', 'status')
    search_fields = ('user__email', 'user__full_name')

@admin.register(TrustActivityLog)
class TrustActivityLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'activity_type', 'score_change', 'created_at')
    list_filter = ('activity_type',)
    search_fields = ('profile__user__email',)

@admin.register(RiskLog)
class RiskLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'severity', 'risk_factor', 'created_at')
    list_filter = ('severity',)
    search_fields = ('profile__user__email', 'risk_factor')
