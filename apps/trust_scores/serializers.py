from rest_framework import serializers
from .models import TrustProfile, TrustActivityLog, RiskLog

class TrustActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustActivityLog
        fields = ['id', 'activity_type', 'score_change', 'reason', 'created_at']

class RiskLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskLog
        fields = ['id', 'risk_factor', 'severity', 'ai_decision', 'created_at']

class TrustProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    activity_logs = TrustActivityLogSerializer(many=True, read_only=True)

    class Meta:
        model = TrustProfile
        fields = '__all__'

    def get_user_name(self, obj):
        u = obj.user
        full = f"{u.first_name} {u.last_name}".strip()
        return full if full else u.email.split('@')[0]
