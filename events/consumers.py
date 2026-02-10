import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    URL: ws://<host>/ws/notifications/<user_id>/
    """

    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notifications_{self.user_id}'

        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"✅ User {self.user_id} connected to notifications")

    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ User {self.user_id} disconnected from notifications")

    async def send_notification(self, event):
        """
        Receive notification from group and send to WebSocket
        """
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': message
        }))
        
        print(f"📤 Sent notification to user {self.user_id}: {message.get('eventTitle', '')}")
