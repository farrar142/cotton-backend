import json
from typing import Any
from asgiref.sync import async_to_sync


from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class UserChatConsumer(AsyncJsonWebsocketConsumer):
    @staticmethod
    def get_group_name(user_id: int | str):
        return f"message_user-{user_id}"

    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = self.get_group_name(self.group_id)
        if self.channel_layer:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.channel_layer:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @classmethod
    def send_message(cls, user_id: int | str, message: dict):
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            cls.get_group_name(user_id),
            dict(type="emit_message", message=message),
        )


class ChatConsumer(AsyncJsonWebsocketConsumer):
    @staticmethod
    def get_group_name(group_id: int | str):
        return f"message_group-{group_id}"

    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.group_name = self.get_group_name(self.group_id)
        if self.channel_layer:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.channel_layer:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def emit_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    @classmethod
    def send_message(cls, group_id: int | str, message: dict):
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            cls.get_group_name(group_id),
            dict(type="emit_message", message=message),
        )
