from typing import Any, Self
from django.db import models

from users.models import User


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def filter(self, *args: Any, **kwargs: Any):
        return super().filter(deleted_at__isnull=True, *args, **kwargs)


class SoftDeleteManager(models.Manager):
    pass


class SoftDeleteModel(models.Model):
    objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)()
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class CommonModel(BaseModel, SoftDeleteModel):
    user_id: int
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @classmethod
    def concrete_queryset(
        cls, *args, replace: models.QuerySet[Self] | None = None, **kwargs
    ):
        qs = cls.objects
        if replace:
            qs = replace
        return qs.prefetch_related(
            models.Prefetch("user", User.concrete_queryset(user=kwargs.get("user")))
        ).all()
