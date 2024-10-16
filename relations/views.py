from rest_framework import exceptions

from django.core.cache import cache

from commons import permissions, paginations
from commons.viewsets.base_viewsets import BaseViewset

from posts.services.recommend_service import RecommendService
from posts.models import Post
from users.serializers import UserSerializer
from .service import FollowService, Follow, User, models


class FollowViewset(BaseViewset[User, User]):
    permission_classes = [permissions.AuthorizedOnly]
    queryset = User.concrete_queryset()
    read_only_serializer = UserSerializer
    pagination_class = paginations.CursorPagination
    action = BaseViewset.action

    def get_queryset(self):
        return User.concrete_queryset(user=self.request.user)

    @action(methods=["GET"], detail=False, url_path="users/recommended")
    def get_recommended_users(self, *args, **kwargs):

        user = self.request.user
        cache_key = f"recommended:users:{user.pk}"
        if not (knn_qs := cache.get(cache_key)):
            posts = RecommendService.get_users_related_posts(self.request.user)
            knn_qs = RecommendService.get_post_knn(posts)
            cache.set(cache_key, knn_qs, timeout=60)
        self.get_queryset = lambda: User.concrete_queryset(
            self.request.user, replace=knn_qs
        )
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=False, url_path="followings")
    def get_followings(self, *args, **kwargs):
        service = FollowService(self.request.user)
        self.override_get_queryset(
            lambda x: service.get_users_followings(self.request.user)
        )
        self.ordering = ("-following_created_at",)
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=True, url_path="followings")
    def get_user_followings(self, *args, **kwargs):
        target_user = self.get_object()
        service = FollowService(self.request.user)
        self.override_get_queryset(lambda x: service.get_users_followings(target_user))
        self.ordering = ("-following_created_at",)
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=False, url_path="followers")
    def get_followers(self, *args, **kwargs):
        service = FollowService(self.request.user)
        self.override_get_queryset(
            lambda x: service.get_users_followers(self.request.user)
        )
        self.ordering = ("-followed_by_created_at",)
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=True, url_path="followers")
    def get_user_followers(self, *args, **kwargs):
        service = FollowService(self.request.user)
        target_user = self.get_object()
        self.override_get_queryset(lambda x: service.get_users_followers(target_user))
        self.ordering = ("-followed_by_created_at",)
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

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"(?P<username>[\w-]+)",
        permission_classes=[],
    )
    def get_profile(self, *args, **kwargs):
        instance = self.get_queryset().filter(username=kwargs["username"]).first()
        if not instance:
            raise exceptions.NotFound
        Serializer = self.get_serializer_class()
        ser = Serializer(instance=instance, context=self.get_serializer_context())
        return self.Response(ser.data)
