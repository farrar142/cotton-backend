from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.decorators import action


from commons import permissions
from commons.viewsets import BaseViewset, ReadOnlyMixin

from ..models import User
from ..serializers import UserSerializer, UserUpsertSerializer


class UserViewSet(BaseViewset[User, User]):
    permission_classes = [permissions.OwnerOrReadOnly]
    queryset = User.concrete_queryset()

    read_only_serializer = UserSerializer
    upsert_serializer = UserUpsertSerializer

    search_fields = ("username", "id")

    def create(self, *args, **kwargs):
        raise self.exceptions.PermissionDenied

    def delete(self, *args, **kwargs):
        raise self.exceptions.PermissionDenied

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.concrete_queryset()
        return User.concrete_queryset(user=self.request.user)

    @action(methods=["GET"], detail=False, url_path="me")
    def me(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            raise exceptions.AuthenticationFailed
        data = self.read_only_serializer(
            instance=self.get_queryset().get(pk=self.request.user.pk)
        ).data
        return Response(data)
