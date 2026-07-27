from rest_framework import serializers
from typing import Optional
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id', 'conversation', 'sender', 'sender_email', 'sender_name',
            'text', 'attachment_url', 'voice_note_url', 'is_seen',
            'created_at', 'timestamp'
        )

    def get_timestamp(self, obj) -> str:
        return obj.created_at.strftime('%H:%M')

class ConversationSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ('id', 'created_at', 'updated_at', 'other_participant', 'last_message', 'unread_count')

    def get_other_participant(self, obj) -> dict:
        request = self.context.get('request')
        if not request or not request.user:
            return {}
        # Find the participant that is not the active request user
        other = obj.participants.exclude(id=request.user.id).first()
        if other:
            return {
                'id': other.id,
                'name': f"{other.first_name} {other.last_name}".strip() or other.email.split('@')[0],
                'email': other.email,
                'role': other.role
            }
        return {}

    def get_last_message(self, obj) -> Optional[dict]:
        last_msg = obj.messages.order_by('created_at').last()
        if last_msg:
            return {
                'text': last_msg.text or '📎 Attachment',
                'timestamp': last_msg.created_at.strftime('%I:%M %p'),
                'is_seen': last_msg.is_seen,
                'sender_id': last_msg.sender.id
            }
        return None

    def get_unread_count(self, obj) -> int:
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        return obj.messages.filter(is_seen=False).exclude(sender=request.user).count()

