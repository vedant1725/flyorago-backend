from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'type', 'is_read', 'createdAt', 'created_at')

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat() if obj.created_at else ''
