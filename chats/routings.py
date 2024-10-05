from django.urls import re_path

from .consumers import ChatConsumer, UserConsumer


websocket_urlpatterns = [
    re_path(r"ws/message_groups/(?P<group_id>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/users/(?P<user_id>\w+)/$", UserConsumer.as_asgi()),
]
