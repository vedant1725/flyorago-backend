from rest_framework import generics, permissions, status, views
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from common.responses import success_response, failure_response

User = get_user_model()

class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        # Conversations where active user is a participant
        return Conversation.objects.filter(participants=self.request.user).prefetch_related('participants', 'messages')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return success_response(data=serializer.data, message="Conversations list retrieved")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        participant_id = request.data.get('participant_id')
        if not participant_id:
            return failure_response(message="participant_id is required")
        
        other_user = get_object_or_404(User, id=participant_id)
        if other_user == request.user:
            return failure_response(message="You cannot start a conversation with yourself")

        # Check for existing chat
        existing = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
        if existing:
            serializer = self.get_serializer(existing, context={'request': request})
            return success_response(data=serializer.data, message="Conversation already exists")

        # Create new chat
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other_user)
        conv.save()

        serializer = self.get_serializer(conv, context={'request': request})
        return success_response(data=serializer.data, message="Conversation created successfully", status_code=status.HTTP_201_CREATED)

class MessageListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conv_id = self.kwargs['conversation_id']
        conv = get_object_or_404(Conversation, id=conv_id, participants=self.request.user)
        
        # Mark all messages sent by the other participant as seen on fetch
        conv.messages.exclude(sender=self.request.user).update(is_seen=True)
        return conv.messages.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Messages fetched")

    def create(self, request, *args, **kwargs):
        conv_id = self.kwargs['conversation_id']
        conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            msg = serializer.save(
                conversation=conv,
                sender=request.user
            )
            # Update conversation timestamp
            conv.save()
            return success_response(data=serializer.data, message="Message sent", status_code=status.HTTP_201_CREATED)
        return failure_response(errors=serializer.errors, message="Failed to send message")
