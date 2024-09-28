from django.apps import apps

from commons import paginations
from commons import permissions
from commons.viewsets import BaseViewset

from images.models import Image
from images.serializers import ImageSerializer
from users.models import User, models
from ..services.post_service import PostService
from ..models import Post
from ..serializers import PostSerializer, FavoriteSerializer

from .child_views import create_bool_child_mixin


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
    pagination_class = paginations.CursorPagination
    ordering = ("-latest_date", "-id")
    ordering_fields = ("-latest_date", "-id")
    filterset_fields = ("user__username",)

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

    @action(methods=["GET"], detail=False, url_path=r"timeline/(?P<username>[\w-]+)")
    def get_user_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = lambda: Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(
            lambda qs: qs.filter(parent__isnull=True).filter(
                models.Q(user=user) | models.Q(reposts__user=user)
            )
        )
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"], detail=False, url_path=r"timeline/(?P<username>[\w-]+)/replies"
    )
    def get_users_replies_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = lambda: Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(
            lambda qs: qs.annotate(
                row_number=models.Window(
                    expression=models.functions.RowNumber(),
                    partition_by=models.F("origin"),
                    order_by=models.F("created_at").desc(),
                )
            ).filter(parent__isnull=False, user=user, row_number=1)
        )
        # is_last_child = models.Window(
        #     expression=models.functions.FirstValue("id"),
        #     partition_by=models.F("origin"),
        #     order_by=models.F("created_at").desc(),
        # )
        # self.override_get_queryset(
        #     lambda qs: qs.annotate(last_child_id=is_last_child)
        #     .filter(last_child_id=models.F("pk"))
        #     .filter(parent__isnull=False, user=user)
        # )
        return self.list(*args, **kwargs)

    @action(
        methods=["GET"], detail=False, url_path=r"timeline/(?P<username>[\w-]+)/media"
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
        url_path=r"timeline/(?P<username>[\w-]+)/favorites",
    )
    def get_users_favorite_timeline(self, *args, **kwargs):
        user = self.get_user_from_queries()
        self.get_queryset = lambda: Post.concrete_queryset(self.request.user, user)
        self.override_get_queryset(lambda qs: qs.filter(favorites__user=user))
        self.ordering = ("-favorites__created_at",)
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
        return self.list(*args, **kwargs)
