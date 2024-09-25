from rest_framework import exceptions
from commons import permissions, paginations
from commons.viewsets.base_viewsets import BaseViewset

from users.serializers import UserSerializer
from .service import FollowService, Follow, User


class FollowViewset(BaseViewset[User, User]):
    permission_classes = [permissions.AuthorizedOnly]
    queryset = User.concrete_queryset()
    read_only_serializer = UserSerializer
    pagination_class = paginations.CursorPagination
    action = BaseViewset.action

    def get_queryset(self):
        return User.concrete_queryset(user=self.request.user)

    @action(methods=["GET"], detail=False, url_path="followings")
    def get_followings(self, *args, **kwargs):
        service = FollowService(self.request.user)
        self.override_get_queryset(lambda x: service.get_followings())
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=False, url_path="followers")
    def get_followers(self, *args, **kwargs):
        service = FollowService(self.request.user)
        self.override_get_queryset(lambda x: service.get_followers())
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=False, url_path="mutual_followings")
    def get_mutual_followings(self, *args, **kwargs):
        service = FollowService(self.request.user)
        self.override_get_queryset(lambda x: service.get_mutual_followings())
        return self.list(*args, **kwargs)

    @action(methods=["POST"], detail=True, url_path="follow")
    def follow(self, *args, **kwargs):
        service = FollowService(self.request.user)
        service.follow(self.get_object())
        return self.result_response(True)

    @follow.mapping.delete
    def unfollow(self, *args, **kwargs):
        service = FollowService(self.request.user)
        service.unfollow(self.get_object())
        return self.result_response(True, 204)

    def create(self, request, *args, **kwargs):
        raise exceptions.NotFound

    def update(self, request, *args, **kwargs):
        raise exceptions.NotFound

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.NotFound

    def destroy(self, request, *args, **kwargs):
        raise exceptions.NotFound
