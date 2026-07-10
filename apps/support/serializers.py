from rest_framework import serializers
from .models import FAQ, Ticket, TicketReply

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer', 'category')

class TicketReplySerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = TicketReply
        fields = ('id', 'sender', 'sender_name', 'message', 'createdAt')
        read_only_fields = ('id', 'sender', 'createdAt')

    def get_sender_name(self, obj) -> str:
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email.split('@')[0]

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

class TicketSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()
    replies = TicketReplySerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = ('id', 'subject', 'category', 'status', 'priority', 'createdAt', 'replies')
        read_only_fields = ('id', 'status', 'createdAt')

    def get_createdAt(self, obj) -> str:
        return obj.created_at.strftime('%Y-%m-%d')

