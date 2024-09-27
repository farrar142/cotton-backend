import time
from typing import Any, Callable, Concatenate, Mapping, ParamSpec, Self, TypeVar
from django.conf import settings
from django.http.response import HttpResponse
from django.test import TestCase as TC, Client as C
from django.contrib.auth import get_user_model

from commons.authentication import CustomTokenObtainPairSerializer

from pprint import pprint as pp

P = ParamSpec("P")
T = TypeVar("T")

User = get_user_model()


def header_override():
    def decorator(func: Callable[Concatenate["Client", P], T]):
        def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
            kwargs["headers"] = self._headers  # type:ignore
            result = func(self, *args, **kwargs)
            result.show = lambda: pp(result.json())  # type:ignore
            return result

        return wrapper

    return decorator


class Client(C):
    _headers = dict()

    def login(self, user: Any):
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        access = str(refresh.access_token)  # type:ignore
        self._headers = dict(AUTHORIZATION=f"Bearer {access}")
        return access, str(refresh)

    @header_override()
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    @header_override()
    def post(self, *args, **kwargs):
        return super().post(content_type="application/json", *args, **kwargs)

    @header_override()
    def patch(self, *args, **kwargs):
        return super().patch(content_type="application/json", *args, **kwargs)

    @header_override()
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)


class TestCase(TC):
    client_class = Client
    client: Client = Client()

    def __init__(self, methodName: str = "runTest") -> None:
        settings.DEBUG = True
        super().__init__(methodName)

    def setUp(self):
        User = get_user_model()
        user = User(username="test", email="test@gmail.com")
        user.set_password("1234567890")
        user2 = User(username="test2", email="test2@gmail.com")
        user2.set_password("1234567890")
        user3 = User(username="test3", email="test3@gmail.com")
        user3.set_password("1234567890")
        users = User.objects.bulk_create([user, user2, user3])
        self.user = users[0]
        self.user2 = users[1]
        self.user3 = users[2]

    def pprint(self, *args, **kwargs):
        pp(*args, **kwargs)
