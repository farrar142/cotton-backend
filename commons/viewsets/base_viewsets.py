from pprint import pprint
from typing import Any, Callable, Generic, Iterable, TypeVar

from rest_framework import exceptions, decorators, serializers
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from django.contrib.auth.models import AbstractBaseUser

from ..requests import Request
from ..serializers import BaseModelSerializer

from django.db import models

from .filterset_viewsets import CustomFiltersetMixin

M = TypeVar("M", bound=models.Model)
U = TypeVar("U", bound=AbstractBaseUser)


class BaseViewset(CustomFiltersetMixin[M, U], ModelViewSet, Generic[M, U]):
    Response = Response
    pprint = pprint
    exceptions = exceptions
    serializers = serializers
    action = decorators.action
    request: Request[U]
    read_only_serializer: type[BaseModelSerializer[M]]
    upsert_serializer: type[BaseModelSerializer[M]]
    ordering: Iterable[str]
    ordering_fields: Iterable[str]
    queryset: models.QuerySet[M]

    _instance: M | None = None

    def get_serializer_class(self):
        if self.request.method == "GET":
            return self.read_only_serializer
        return self.upsert_serializer

    def get_object(self) -> M:
        if self._instance == None:
            self._instance = super().get_object()
        return self._instance  # type: ignore

    def get_queryset(self):
        return self.queryset

    @decorators.action(methods=["GET"], detail=False, url_path="flat")
    def flat_items(self, *args, **kwargs):
        self.pagination_class = None
        return self.list(*args, **kwargs)

    @decorators.action(methods=["GET"], detail=False, url_path="count")
    def get_count(self, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        return self.Response({"count": qs.count()})

    def result_response(self, result: bool, status_code=201):
        return self.Response(dict(is_success=result), status=status_code)

    def override_get_queryset(
        self, qs_func: Callable[[models.QuerySet[M]], models.QuerySet[M]]
    ):
        gqs = self.get_queryset

        def get_queryset(*args, **kwargs):
            return qs_func(gqs())

        self.get_queryset = get_queryset
