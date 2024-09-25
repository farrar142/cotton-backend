from typing import Callable
from rest_framework import exceptions
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


@create_bool_child_mixin[Post](
    url_path="reposts",
    override_get_qs=lambda vs, qs: qs.filter(has_repost=True),
    get_qs=lambda qs: qs.reposts,
)
@create_bool_child_mixin[Post](
    url_path="bookmarks",
    override_get_qs=lambda vs, qs: qs.filter(has_bookmark=True),
    get_qs=lambda qs: qs.bookmarks,
)
@create_bool_child_mixin[Post](
    url_path="favorites",
    override_get_qs=lambda vs, qs: qs.filter(has_favorite=True),
    get_qs=lambda qs: qs.favorites,
)
class PostViewSet(BaseViewset[Post, User]):
    permission_classes = [permissions.AuthorizedOrReadOnly]
    queryset = Post.concrete_queryset()
    read_only_serializer = PostSerializer
    upsert_serializer = PostSerializer
    pagination_class = LatestOrderedCursorPagination
    ordering = ("-latest_date",)

    action = BaseViewset.action

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Post.concrete_queryset(user=self.request.user)
        return Post.concrete_queryset()

    @action(
        methods=["GET"],
        detail=False,
        url_path="timeline",
        permission_classes=[permissions.AuthorizedOnly],
    )
    def get_timeline(self, *args, **kwargs):

        return self.list(*args, **kwargs)
