from functools import wraps
from typing import Any, Callable, Generic, ParamSpec, TypeVar

from django.db import models

from commons import serializers

from users.serializers import UserSerializer


T = TypeVar("T", bound=models.Model)
P = ParamSpec("P")


class DummyRequest:
    user: Any | None = None


def _inject_user(function: Callable[P, dict]):
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        serializer: serializers.BaseModelSerializer = args[0]  # type:ignore
        validated_data: dict = args[-1]  # type:ignore
        request = serializer.context.get("request", DummyRequest)
        validated_data["user"] = request.user

        return function(*args, **kwargs)

    return wrapper


def inject_user(
    _kls: type[serializers.BaseModelSerializer[T]],
) -> type[serializers.BaseModelSerializer[T]]:
    Meta = _kls.Meta
    Meta.fields = (*Meta.fields, "user")

    class UserSupported(_kls):
        user = UserSerializer(read_only=True)

        @_inject_user
        def create(self, validated_data):
            return super().create(validated_data)

    UserSupported.__name__ = _kls.__name__
    return UserSupported
