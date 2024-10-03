import json
from typing import Any


from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncJsonWebsocketConsumer


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
        layer = get_channel_layer()
        if layer:
            layer.group_send(self.group_name, "hello")

    async def disconnect(self, close_code):
        if self.channel_layer:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
