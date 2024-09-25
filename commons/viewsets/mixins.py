from typing import TypeVar
from django.db import models

from rest_framework import exceptions

type T = models.Model


class ReadOnlyMixin[T]:
    def create(self, *args, **kwargs):
        raise exceptions.PermissionDenied("Forbidden Method")

    def update(self, *args, **kwargs):
        raise exceptions.PermissionDenied("Forbidden Method")

    def destroy(self, *args, **kwargs):
        raise exceptions.PermissionDenied("Forbidden Method")
