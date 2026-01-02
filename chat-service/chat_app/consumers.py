from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from urllib.parse import parse_qs
import uuid
from django.db import IntegrityError


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")
        self.room_group_name = None

        if not user or "user_id" not in user or "role" not in user:
            await self.close()
            return

        query = parse_qs(self.scope["query_string"].decode())
        query_id = query.get("vendor_id", [None])[0]

        if not query_id:
            await self.close()
            return

        if user["role"] == "vendor":
            # For vendors, their own ID is the vendor_id
            # The query_id is the user_id (customer they are talking to)
            self.vendor_id = user["user_id"]
            self.user_id = int(query_id)
        else:
            # For customers, their own ID is the user_id
            # The query_id is the vendor_id
            self.user_id = user["user_id"]
            self.vendor_id = int(query_id)

        self.room_group_name = f"chat_u{self.user_id}_v{self.vendor_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data):
        user = self.scope["user"]

        try:
            data = json.loads(text_data)
            message = data["message"]
            message_id = data["message_id"]
            uuid.UUID(message_id)  # validate UUID format
        except Exception:
            return  # invalid payload → drop

        sender = user.get("role")
        if sender not in ("customer", "vendor"):
            print(f"WS REJECT: Invalid role '{sender}'")
            return

        # Ensure IDs are integers
        try:
            target_user_id = int(self.user_id)
            target_vendor_id = int(self.vendor_id)
        except (ValueError, TypeError):
            print(f"ERROR: Invalid IDs in WebSocket: user={self.user_id}, vendor={self.vendor_id}")
            return

        saved = await self.save_message(
            message_id=message_id,
            user_id=target_user_id,
            vendor_id=target_vendor_id,
            sender_type=sender,
            message=message,
        )

        if not saved:
            print(f"WARNING: Message {message_id} not saved (possible duplicate)")
            return  # duplicate → ignore

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                "sender": sender,
                "message_id": message_id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    
    @database_sync_to_async
    def save_message(self, message_id, user_id, vendor_id, sender_type, message):
        from .models import ChatMessage

        try:
            ChatMessage.objects.create(
                message_id=message_id,
                user_id=user_id,
                vendor_id=vendor_id,
                sender_type=sender_type,
                message=message
            )
            return True
        except IntegrityError:
            # message_id already exists → duplicate
            return False