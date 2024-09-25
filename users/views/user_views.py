from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.decorators import action


from commons.viewsets import BaseViewset, ReadOnlyMixin

from ..models import User
from ..serializers import UserSerializer


class UserViewSet(BaseViewset[User, User], ReadOnlyMixin[User]):
    queryset = User.concrete_queryset()

    read_only_serializer = UserSerializer
    upsert_serializer = UserSerializer

    search_fields = ("username", "id")

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
