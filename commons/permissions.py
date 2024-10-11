from django.contrib.auth.models import AnonymousUser, AbstractUser

from rest_framework import exceptions
from rest_framework.permissions import BasePermission, SAFE_METHODS

from commons.requests import Request


class AuthorizedOnly(BasePermission):
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            raise exceptions.NotAuthenticated
        return super().has_permission(request, view)


class AuthorizedOrReadOnly(BasePermission):
    def has_permission(self, request: Request[AbstractUser], view):
        if request.method in SAFE_METHODS:
            return True
        if isinstance(request.user, AnonymousUser):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if isinstance(request.user, AnonymousUser):
            return False
        if request.user.pk != obj.user_id:
            return False
        return True


class OwnerOrReadOnly(AuthorizedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if isinstance(request.user, AnonymousUser):
            return False
        if request.user.pk != getattr(obj, "user_id", getattr(obj, "id", None)):
            return False
        return True


class AdminOrReadOnly(BasePermission):
    def has_permission(self, request: Request[AbstractUser], view):
        if request.method in SAFE_METHODS:
            return True
        if isinstance(request.user, AnonymousUser):
            return False
        if not request.user.is_staff:
            return False
        return True
