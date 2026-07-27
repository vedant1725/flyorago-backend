from rest_framework import serializers
from .models import FAQ, Ticket, TicketReply, Dispute, DisputeImage
from bookings.serializers import BookingSerializer

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

class DisputeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisputeImage
        fields = ('id', 'image', 'uploaded_at')

class DisputeSerializer(serializers.ModelSerializer):
    images = DisputeImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dispute
        fields = ('id', 'booking', 'raised_by', 'reason', 'description', 'status', 'resolution', 'created_at', 'images')
        read_only_fields = ('id', 'raised_by', 'status', 'resolution', 'created_at')

class AdminDisputeSerializer(serializers.ModelSerializer):
    images = DisputeImageSerializer(many=True, read_only=True)
    raised_by_name = serializers.SerializerMethodField()
    raised_by_email = serializers.SerializerMethodField()
    booking_details = BookingSerializer(source='booking', read_only=True)
    
    class Meta:
        model = Dispute
        fields = ('id', 'booking', 'booking_details', 'raised_by', 'raised_by_name', 'raised_by_email', 'reason', 'description', 'status', 'resolution', 'created_at', 'images')
        
    def get_raised_by_name(self, obj):
        return f"{obj.raised_by.first_name} {obj.raised_by.last_name}".strip()
        
    def get_raised_by_email(self, obj):
        return obj.raised_by.email
