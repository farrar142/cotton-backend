import json
from typing import Any
from asgiref.sync import async_to_sync, sync_to_async


from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class UserConsumer(AsyncJsonWebsocketConsumer):
    signed = False

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

    async def receive_json(self, content, **kwargs):
        if not (access := content.get("access", None)):
            return
        try:
            from commons.authentication import CustomJWTAuthentication

            auth = CustomJWTAuthentication()
            if not (user := auth.get_cached_user(access)):
                raw_token = auth.get_validated_token(access.encode())
                user = await sync_to_async(auth.get_user)(raw_token)
            if int(self.group_id) == user.pk:
                self.signed = True
            else:
                await self.send(json.dumps(dict(type="authorization", result=False)))
        except:
            print("exception")
            await self.send(json.dumps(dict(type="authorization", result=False)))

    async def emit_event(self, event):
        if not self.signed:
            return
        data = event["data"]
        await self.send(text_data=json.dumps(data))

    @classmethod
    def send_message(cls, user_id: int | str, message: dict):
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            cls.get_group_name(user_id),
            dict(type="emit_event", data=dict(type="message", message=message)),
        )

    @classmethod
    def send_group_message(cls, user_id: int | str, message_group_id: int):

        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            cls.get_group_name(user_id),
            dict(
                type="emit_event",
                data=dict(type="group", state="changed", id=message_group_id),
            ),
        )

    @classmethod
    def send_group_user_exit(cls, user_id: int, message_group_id: int, exit_user: int):
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            cls.get_group_name(user_id),
            dict(
                type="emit_event",
                data=dict(
                    type="group",
                    state="user_exit",
                    id=message_group_id,
                    exit_user=exit_user,
                ),
            ),
        )

    @classmethod
    def send_notification(cls, user_id: int | str, message: dict):
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            cls.get_group_name(user_id),
            dict(
                type="emit_event", data=dict(type="notification", notification=message)
            ),
        )
