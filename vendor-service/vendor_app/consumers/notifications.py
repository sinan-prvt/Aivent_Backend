import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        
        if not self.user:
            logger.warning("WebSocket connection rejected: Unauthenticated")
            await self.close()
            return

        self.user_id = self.user["user_id"]
        self.role = self.user.get("role")

        # Dynamic groups based on user ID and role
        self.user_group = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        if self.role:
            self.role_group = f"role_{self.role}"
            await self.channel_layer.group_add(self.role_group, self.channel_name)

        await self.accept()
        logger.info(f"WebSocket connected: User {self.user_id} (Role: {self.role})")

    async def disconnect(self, close_code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        
        if hasattr(self, "role_group"):
            await self.channel_layer.group_discard(self.role_group, self.channel_name)
        
        logger.info(f"WebSocket disconnected: User {getattr(self, 'user_id', 'Unknown')}")

    async def notify_new(self, event):
        """
        Handler for NEW_NOTIFICATION signal from channel layer
        """
        await self.send(text_data=json.dumps(event))
