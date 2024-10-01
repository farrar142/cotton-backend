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

    search_fields = ("nickname", "username")

    def create(self, *args, **kwargs):
        raise self.exceptions.PermissionDenied

    def delete(self, *args, **kwargs):
        raise self.exceptions.PermissionDenied

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.concrete_queryset()
        return User.concrete_queryset(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        instance.refresh_from_db()
        serializer = UserSerializer(instance, context=self.get_serializer_context())
        return self.Response(serializer.data)

    @action(methods=["GET"], detail=False, url_path="me")
    def me(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            raise exceptions.AuthenticationFailed
        data = self.read_only_serializer(
            instance=self.get_queryset().get(pk=self.request.user.pk)
        ).data
        return Response(data)
