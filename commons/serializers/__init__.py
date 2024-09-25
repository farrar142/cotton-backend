from typing import Any, Generic, Sequence, TypeVar

import base64

from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import serializers, exceptions
from rest_framework.serializers import ModelSerializer, Serializer

from django.db import models

M = TypeVar("M", bound=models.Model)


class Meta(Generic[M]):
    model: type[M]
    fields: Sequence[str]


def inject_context(self: Any, user: Any):
    class Request:
        pass

    request = self.context.get("request", Request)

    request.user = user  # type:ignore
    self.context["request"] = request


class BaseModelSerializer(ModelSerializer, Generic[M]):
    Meta: type[Meta]

    def __init__(self, *args, queryset: models.QuerySet[M] | None = None, **kwargs):
        self.queryset = queryset
        user = kwargs.pop("user", None)
        super(ModelSerializer, self).__init__(*args, **kwargs)
        if user:
            inject_context(self, user)

    def to_internal_value(self, data):
        if isinstance(data, int):
            if self.queryset == None:
                raise exceptions.ValidationError(detail=["쿼리셋이 설정되지 않았음."])
            return self.queryset.get(pk=data)
        return super().to_internal_value(data)


class Base64Serializer(serializers.ImageField):
    def to_internal_value(self, data: str):
        data = data.split(",")[-1]
        bytes_str = bytes(data, encoding="raw_unicode_escape")
        file = SimpleUploadedFile(
            "image.png", base64.b64decode(bytes_str), content_type="image/png"
        )
        return super().to_internal_value(file)
