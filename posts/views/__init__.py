from django.apps import apps

from commons import paginations
from commons import permissions
from commons.viewsets import BaseViewset

from users.models import User, models
from ..services.post_service import PostService
from ..models import Post
from ..serializers import PostSerializer, FavoriteSerializer

from .child_views import create_bool_child_mixin


class LatestOrderedCursorPagination(paginations.CursorPagination):
    ordering = ("-latest_date", "-id")


class IdOrderedCursorPagination(paginations.CursorPagination):
    ordering = ("-id",)


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
    read_only_serializer = PostSerializer
    upsert_serializer = PostSerializer
    pagination_class = LatestOrderedCursorPagination
    ordering = ("-latest_date",)
    ordering_fields = ("-latest_date", "-id")
    filterset_fields = ("user__username",)

    action = BaseViewset.action

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Post.concrete_queryset(user=self.request.user)
        return Post.concrete_queryset()

    @action(methods=["GET"], detail=False, url_path=r"timeline/(?P<username>[\w-]+)")
    def get_user_timeline(self, *args, **kwargs):
        user = User.objects.filter(username=kwargs[""]).first()
        if not user:
            raise self.exceptions.NotFound
        self.queryset = Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(
            lambda qs: qs.filter(models.Q(user=user) | models.Q(reposts__user=user))
        )
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
                models.Q(user__followers__followed_by=self.request.user)
                | models.Q(user=self.request.user)
                | models.Q(has_repost=True)
            )
        )

        return self.list(*args, **kwargs)

    @action(
        methods=["GET"], detail=False, url_path="timeline/global", permission_classes=[]
    )
    def get_global_timeline(self, *args, **kwargs):
        self.ordering = ("-id",)
        self.pagination_class = IdOrderedCursorPagination
        return self.list(*args, **kwargs)
