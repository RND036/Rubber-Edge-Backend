import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from urllib.parse import parse_qs

from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        # ✅ Extract client ID properly
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)
        client_id = query_params.get('client', ['unknown'])[0]
        
        print(f"🔌 CONNECT: user={self.scope['user'].id} | client={client_id} | convo={self.conversation_id} | channel={self.channel_name}")

        user = self.scope["user"]
        if not user.is_authenticated:
            print(f"❌ AUTH FAIL: {user}")
            await self.close()
            return

        is_member = await self.user_in_conversation(user.id, self.conversation_id)
        if not is_member:
            print(f"❌ NOT MEMBER: user={user.id} convo={self.conversation_id}")
            await self.close()
            return

        print(f"✅ JOINED: {self.channel_name} → {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f"🔌 DISCONNECT: {self.channel_name} from {self.room_group_name} (code={close_code})")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        text = data.get("text", "").strip()
        if not text:
            return

        print(f"📨 RECEIVE: '{text}' from user={self.scope['user'].id} in convo={self.conversation_id}")

        user = self.scope["user"]
        msg = await self.create_message(user.id, self.conversation_id, text)

        print(f"📢 BROADCAST to {self.room_group_name}: msg ID={msg['id']} to convo {self.conversation_id}")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                **msg,
            },
        )

    async def chat_message(self, event):
        print(f"📥 DELIVER to {self.channel_name}: '{event['text'][:20]}...' (ID={event['id']})")
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def user_in_conversation(self, user_id, convo_id):
        return Conversation.objects.filter(
            Q(id=convo_id) & (Q(farmer_id=user_id) | Q(officer_id=user_id))
        ).exists()

    @database_sync_to_async
    def create_message(self, user_id, convo_id, text):
        convo = Conversation.objects.get(id=convo_id)
        msg = Message.objects.create(
            conversation=convo,
            sender_id=user_id,
            text=text,
        )
        return {
            "id": msg.id,
            "conversation": convo_id,
            "sender_id": user_id,
            "text": msg.text,
            "created_at": msg.created_at.isoformat(),
        }
