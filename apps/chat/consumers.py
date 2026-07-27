import json
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class ChatConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Join conversation room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave conversation room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive_json(self, content):
        message_text = content.get('message')
        sender_id = content.get('sender_id')

        if not message_text or not sender_id:
            return

        try:
            sender = User.objects.get(id=sender_id)
            conversation = Conversation.objects.get(id=self.conversation_id)
            
            # Persist message to database
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                text=message_text
            )
            
            # Broadcast message event to Channels group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_text,
                    'sender_id': sender.id,
                    'sender_email': sender.email,
                    'timestamp': message.created_at.strftime('%H:%M')
                }
            )
        except Exception as e:
            self.send_json({'error': str(e)})

    def chat_message(self, event):
        # Send event packet down the active WebSocket connection
        self.send_json({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_email': event['sender_email'],
            'timestamp': event['timestamp']
        })
