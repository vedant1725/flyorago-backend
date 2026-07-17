import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We assume the user ID is passed in the URL, e.g. /ws/notifications/1/
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f"user_{self.user_id}_notifications"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def payment_secured(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'payment_secured',
            'notification_id': event['notification_id'],
            'title': event['title'],
            'message': event['message'],
            'booking_id': event['booking_id']
        }))
        
    async def new_match(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_match',
            'message': event['message']
        }))
