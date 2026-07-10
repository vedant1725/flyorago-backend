from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'type', 'is_read', 'createdAt')

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
