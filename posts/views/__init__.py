from typing import Literal
from django.apps import apps
from django.utils.timezone import localtime
from django.core.cache import cache

from rest_framework import serializers

from commons import paginations
from commons import permissions
from commons.caches import TimeoutCache
from commons.requests import Request
from commons.utils.get_client_ip import get_client_ip
from commons.viewsets import BaseViewset

from images.models import Image
from images.serializers import ImageSerializer
from users.models import User, models
from relations.models import Follow
from ..services.recommend_service import RecommendService
from ..models import Post
from ..serializers import PostSerializer, FavoriteSerializer, PostReadOnlySerializer

from .child_views import create_bool_child_mixin

from ..documents import PostDocument


class SessionSizeSerializer(serializers.Serializer):
    session_min_size = serializers.IntegerField(default=500)


@create_bool_child_mixin[Post](
    model_path="posts.Post",
    url_path="views",
    override_get_qs=lambda vs, qs: qs.filter(has_view=True),
    child_str="views",
)
@create_bool_child_mixin[Post](
    model_path="posts.Post",
    url_path="reposts",
    override_get_qs=lambda vs, qs: qs.filter(has_repost=True),
    child_str="reposts",
)
@create_bool_child_mixin[Post](
    model_path="posts.Post",
    url_path="bookmarks",
    override_get_qs=lambda vs, qs: qs.filter(has_bookmark=True),
    child_str="bookmarks",
)
@create_bool_child_mixin[Post](
    model_path="posts.Post",
    url_path="favorites",
    override_get_qs=lambda vs, qs: qs.filter(has_favorite=True),
    child_str="favorites",
)
class PostViewSet(BaseViewset[Post, User]):
    permission_classes = [permissions.AuthorizedOrReadOnly]
    queryset = Post.concrete_queryset()
    read_only_serializer = PostReadOnlySerializer
    upsert_serializer = PostSerializer
    pagination_class = paginations.TimelinePagination
    offset_field = "latest_date"
    filterset_fields = ("user__username", "origin", "parent")
    search_fields = ("text",)

    action = BaseViewset.action

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Post.concrete_queryset(user=self.request.user)
        return Post.concrete_queryset()

    def get_user_from_queries(self):
        user = User.objects.filter(username=self.kwargs.get("username", None)).first()
        if not user:
            raise self.exceptions.NotFound
        return user

    def get_custom_filterset(self, queryset: models.QuerySet[Post]):
        qs = queryset.annotate(is_user_protected=models.F("user__is_protected"))
        if not self.request.user.is_authenticated:
            return qs.filter(models.Q(is_user_protected=False))
        # post__user가 request.user를 팔로우중인지 알아야됨
        # Follow의 followed_by=post__user와 following_to=request.user를 사용
        return qs.filter(
            models.Q(is_user_protected=False)  # 모든 유저
            | models.Q(
                models.Q(is_user_protected=True)
                & models.Q(
                    models.Q(
                        user=self.request.user
                    )  # 프로텍트 되어있지만 나의 글인경우
                    | models.Q(
                        is_post_user_following_request_user=True,
                        is_user_following_post_user=True,
                    )  # 서로 팔로우 하는 경우
                )
            )
        )

    def list(self, request, *args, **kwargs):
        self.override_get_queryset(lambda qs: qs.filter(deleted_at__isnull=True))
        return super().list(request, *args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"timeline/recommended",
        permission_classes=[permissions.AuthorizedOnly],
    )
    def get_recommended_post(self, *args, **kwargs):
        user = self.request.user
        cache_key = f"recommended:posts:{user.pk}"
        if not (knn_qs := cache.get(cache_key)):
            posts = RecommendService.get_users_related_posts(self.request.user)
            knn_qs = RecommendService.get_post_knn(posts)
            cache.set(cache_key, knn_qs, timeout=60)
        self.get_queryset = lambda: Post.concrete_queryset(
            self.request.user, replace=knn_qs
        ).exclude(user=self.request.user)
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"timeline/recommended/tags",
        permission_classes=[],
    )
    def get_recommended_tags(self, *args, **kwargs):
        tags = RecommendService.get_top_terms_hashtag()
        return self.Response(tags)

    @action(methods=["GET"], detail=False, url_path=r"timeline/search")
    def get_es_search(self, *args, **kwargs):
        search = self.request.query_params.get("search", "")
        self.filter_queryset = lambda x: self.get_custom_filterset(x)  # type:ignore
        if search:
            qs = (
                PostDocument.search()
                .query(
                    "multi_match",
                    fields=[
                        "text",
                        "user.nickname",
                        "user.username",
                        "hashtags[].text",
                    ],
                    query=search,
                )[:300]
                .to_queryset()
            )
            self.get_queryset = lambda: Post.concrete_queryset(
                self.request.user, replace=qs
            )
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"timeline/username/(?P<username>[\w-]+)",
    )
    def get_user_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = lambda: Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(
            lambda qs: qs.filter(models.Q(user=user) | models.Q(reposts__user=user))
        )
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"timeline/username/(?P<username>[\w-]+)/replies",
    )
    def get_users_replies_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = lambda: Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(
            lambda qs: qs.filter(parent__isnull=False, user=user)
        )
        self.offset_field = "created_at"
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"timeline/username/(?P<username>[\w-]+)/media",
    )
    def get_users_media_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = (
            lambda: Post.concrete_queryset(self.request.user, user)
            .annotate(
                has_image=models.Exists(
                    Image.objects.filter(post=models.OuterRef("pk"))
                )
            )
            .filter(has_image=True, user=user)
        )
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path=r"timeline/username/(?P<username>[\w-]+)/favorites",
    )
    def get_users_favorite_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = lambda: Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(lambda qs: qs.filter(favorites__user=user))
        self.offset_field = "favorites__created_at"
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"],
        detail=False,
        url_path="timeline/followings",
        permission_classes=[permissions.AuthorizedOnly],
    )
    def get_timeline(self, *args, **kwargs):
        self.override_get_queryset(
            lambda qs: qs.filter(
                models.Q(is_post_user_following_request_user=True)
                | models.Q(user=self.request.user)
                | models.Q(has_repost=True)
            )
        )

        return self.list(*args, **kwargs)

    def get_session_key(self):
        key = f"cached_sessions/v2:{get_client_ip(self.request)}"
        if self.request.user.is_authenticated:
            key = f"cached_sessions/v2:{self.request.user.pk}"
        return key

    @action(
        methods=["GET"], detail=False, url_path="timeline/global", permission_classes=[]
    )
    def get_global_timeline(self, *args, **kwargs):
        s = SessionSizeSerializer(data=self.request.query_params)
        _, session_min_size = (
            s.is_valid(raise_exception=True),
            s.data["session_min_size"],  # type:ignore
        )
        self.offset_field = "id"
        key = self.get_session_key()
        saved_session: list[int] | None = cache.get(key)
        if not saved_session:
            with TimeoutCache("post_recommended/v2") as pcache:
                saved_session = pcache.counter()
                if len(saved_session) < session_min_size:
                    return self.list(*args, **kwargs)

                cache.set(key, saved_session, timeout=300)
        preserved = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(saved_session)]
        )
        self.override_get_queryset(
            lambda qs: qs.filter(id__in=saved_session).order_by(preserved)
        )
        return self.list(*args, **kwargs)

    @action(methods=["GET"], detail=True, url_path="replies")
    def get_replies(self, *args, **kwargs):
        instance = self.get_object()
        self.override_get_queryset(lambda qs: qs.filter(parent=instance))
        self.offset_field = "created_at"
        return self.list(*args, **kwargs)

    def perform_destroy(self, instance):
        instance.deleted_at = localtime()
        instance.save()
