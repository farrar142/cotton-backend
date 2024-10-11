from typing import Callable, Generic, Self, TypeVar
from django.apps import apps

from rest_framework import exceptions

from commons import permissions
from commons.viewsets.base_viewsets import BaseViewset

from users.models import User, models
from ..tasks import create_child_model

M = TypeVar("M", bound=models.Model)
C = TypeVar("C", bound=models.Model)
U = TypeVar("U", bound=User)


class create_bool_child_mixin(Generic[M]):
    @property
    def Model(self) -> type[M]:
        splitted = self.model_path.split(".")
        return apps.get_model(splitted[0], splitted[1])  # type:ignore

    def get_qs(self, instance: M) -> models.Manager[M]:
        if getattr(instance, "is_deleted", False):
            raise exceptions.NotFound
        return getattr(instance, self.child_str)

    def __init__(
        self,
        model_path: str,
        url_path: str,
        override_get_qs: Callable[
            [BaseViewset[M, User], models.QuerySet[M]], models.QuerySet[M]
        ],
        child_str: str,
    ):
        self.model_path = model_path
        self.url_path, self.override_get_qs, self.child_str = (
            url_path,
            override_get_qs,
            child_str,
        )

    def __call__(self, kls: type[BaseViewset[M, User]]) -> type[BaseViewset[M, User]]:
        class Mixin(kls):
            @staticmethod
            def _get_items():
                def get_items(inner: Self, *args, **kwargs):
                    if not inner.request.user.is_authenticated:
                        raise inner.exceptions.NotAuthenticated()

                    inner.override_get_queryset(
                        lambda x: self.override_get_qs(inner, x)
                    )
                    return super().list(*args, **kwargs)

                get_items.__name__ = f"get_{self.url_path}"
                get_items = BaseViewset.action(
                    methods=["GET"], detail=False, url_path=self.url_path
                )(get_items)
                return get_items

            @staticmethod
            def _create_items():
                def create_items(inner: Self, *args, **kwargs):
                    instance = inner.get_object()
                    create_child_model.delay(
                        self.model_path,
                        self.child_str,
                        instance.pk,
                        inner.request.user.pk,
                    )
                    # self.get_qs(instance).create(user=inner.request.user)
                    return inner.result_response(True)

                create_items.__name__ = f"create_{self.url_path}"
                return create_items

            @staticmethod
            def _delete_items():
                def delete_items(inner: Self, *args, **kwargs):
                    instance = inner.get_object()
                    favorite = (
                        self.get_qs(instance)
                        .filter(user_id=inner.request.user.pk)
                        .first()
                    )
                    if not favorite:
                        return inner.Response(status=204)
                    favorite.delete()
                    return inner.Response(status=204)

                delete_items.__name__ = f"delete_{self.url_path}"
                return delete_items

            @staticmethod
            def _has_items():
                def has_items(inner: Self, *args, **kwargs):
                    if not inner.request.user.is_authenticated:
                        raise exceptions.NotAuthenticated()
                    instance = inner.get_object()
                    favorite = (
                        self.get_qs(instance)
                        .filter(user_id=inner.request.user.pk)
                        .first()
                    )
                    if not favorite:
                        return inner.result_response(False, 200)
                    return inner.result_response(True, 200)

                has_items.__name__ = f"has_{self.url_path}"
                return has_items

        create_items = BaseViewset.action(
            methods=["POST"],
            detail=True,
            url_path=self.url_path,
            permission_classes=[permissions.AuthorizedOnly],
        )(Mixin._create_items())
        delete_items = create_items.mapping.delete(Mixin._delete_items())
        has_items = create_items.mapping.get(Mixin._has_items())

        setattr(Mixin, f"get_{self.url_path}", Mixin._get_items())
        setattr(Mixin, f"create_{self.url_path}", create_items)

        setattr(Mixin, f"delete_{self.url_path}", delete_items)
        setattr(Mixin, f"has_{self.url_path}", has_items)
        Mixin.__name__ = kls.__name__
        return Mixin
