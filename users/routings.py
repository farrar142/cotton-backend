from django.urls import re_path

from .consumers import UserConsumer


websocket_urlpatterns = [
    re_path(r"ws/users/(?P<user_id>\w+)/$", UserConsumer.as_asgi()),
]
