from typing import Generic, Literal, TypeVar
from django.contrib.auth.models import AbstractBaseUser
from rest_framework import request

T = TypeVar("T", bound=AbstractBaseUser)


class Request(request.Request, Generic[T]):
    META: dict[str, str]
    user: T
    method: (
        Literal["GET"]
        | Literal["POST"]
        | Literal["PUT"]
        | Literal["DELETE"]
        | Literal["PATCH"]
    ) = "GET"
