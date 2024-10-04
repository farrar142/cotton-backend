from django.urls import re_path

from .consumers import ChatConsumer, UserChatConsumer


websocket_urlpatterns = [
    re_path(r"ws/message_groups/(?P<group_id>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/message_users/(?P<user_id>\w+)/$", UserChatConsumer.as_asgi()),
]
