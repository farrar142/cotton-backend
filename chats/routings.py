from django.urls import re_path

from .consumers import ChatConsumer


websocket_urlpatterns = [
    re_path(r"ws/message_groups/(?P<group_id>\w+)/$", ChatConsumer.as_asgi())
]
