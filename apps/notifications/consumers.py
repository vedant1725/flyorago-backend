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
    async def user_notification(self, event):
        await self.send(text_data=json.dumps(event))

    async def payment_secured(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'payment_secured',
            'notification_id': event.get('notification_id'),
            'title': event.get('title', '💰 Payment Secured'),
            'message': event.get('message', 'Escrow funds deposited.'),
            'booking_id': event.get('booking_id')
        }))
        
    async def new_match(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_match',
            'title': event.get('title', '✨ New Match Found'),
            'message': event.get('message', '')
        }))

    async def booking_status_update(self, event):
        status_name = str(event.get('status', 'Updated')).replace('_', ' ').title()
        title = event.get('title') or f"Trip & Booking Update: {status_name}"
        await self.send(text_data=json.dumps({
            'type': 'booking_status_update',
            'title': title,
            'message': event.get('message', f"Booking status has changed to {status_name}."),
            'event_type': event.get('event_type'),
            'booking_id': event.get('booking_id'),
            'status': event.get('status')
        }))

    async def dispute_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def wallet_update(self, event):
        await self.send(text_data=json.dumps(event))
