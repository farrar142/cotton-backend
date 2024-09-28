from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from commons.model_utils import make_property_field
from commons.models import CommonModel
from users.models import User
from images.models import Image


class Post(CommonModel):
    origin = models.ForeignKey(
        "Post", on_delete=models.DO_NOTHING, related_name="childrens", null=True
    )
    parent = models.ForeignKey(
        "Post", on_delete=models.DO_NOTHING, related_name="replies", null=True
    )
    depth = models.IntegerField(default=0)
    text = models.TextField(max_length=1024)
    blocks = models.JSONField(default=list)
    images: "models.ManyToManyField[Image,Post]" = models.ManyToManyField(Image)

    views: "models.Manager[View]"
    favorites: "models.Manager[Favorite]"
    bookmarks: "models.Manager[Bookmark]"
    reposts: "models.Manager[Repost]"
    mentions: "models.Manager[Mention]"

    favorites_count = make_property_field(0)
    views_count = make_property_field(0)
    replies_count = make_property_field(0)
    has_views = make_property_field(False)
    has_favorite = make_property_field(False)
    has_bookmark = make_property_field(False)
    has_repost = make_property_field(False)
    relavant_repost: "list[Repost]|None"  # prefetch의 to_attr은 getter setter를 통하여 할당이 불가능해 보임

    @classmethod
    def __concrete_qs_base(cls, user: AbstractBaseUser | None = None):
        if user and not user.is_authenticated:
            user = None
        return (
            super()
            .concrete_queryset(user=user)
            .prefetch_related(
                "images",
                models.Prefetch(
                    "mentions",
                    Mention.objects.prefetch_related(
                        models.Prefetch(
                            "mentioned_to", User.concrete_queryset(user=user)
                        )
                    ).all(),
                ),
                cls.get_latest_relevant_repost(user=user),
            )
            .annotate(
                views_count=cls.get_views_count(),
                favorites_count=cls.get_favorites_count(),
                replies_count=cls.get_replies_count(),
                has_view=cls.get_has_view(user),
                has_favorite=cls.get_has_favorite(user),
                has_bookmark=cls.get_has_bookmark(user),
                has_repost=cls.get_has_repost(user),
            )
        )

    @classmethod
    def concrete_queryset(
        cls,
        user: AbstractBaseUser | None = None,
        target_user: AbstractBaseUser | None = None,
    ):
        if user and not user.is_authenticated:
            user = None
        repost_filter = models.Q(user__followers__followed_by=user) | models.Q(
            user=user
        )
        if target_user and not target_user.is_authenticated:
            target_user = None
            repost_filter = models.Q(user=user) | models.Q(user=target_user)
        return cls.__concrete_qs_base(user).annotate(
            latest_date=models.functions.Coalesce(
                models.Subquery(
                    Repost.objects.filter(post=models.OuterRef("pk"))
                    .filter(repost_filter)
                    .order_by("-created_at")
                    .values("created_at")[:1],
                ),
                models.F("created_at"),
            ),
        )

    @classmethod
    def get_views_count(
        cls,
    ):
        return models.Count("views")

    @classmethod
    def get_has_view(cls, user: AbstractBaseUser | None = None):
        if user == None:
            return models.Value(False)
        return models.Exists(
            View.objects.filter(user=user, post_id=models.OuterRef("pk"))
        )

    @classmethod
    def get_favorites_count(
        cls,
    ):
        return models.Count("favorites")

    @classmethod
    def get_replies_count(cls):
        return models.Count("replies")

    @classmethod
    def get_has_favorite(cls, user: AbstractBaseUser | None = None):
        if user == None:
            return models.Value(False)
        return models.Exists(
            Favorite.objects.filter(user=user, post_id=models.OuterRef("pk"))
        )

    @classmethod
    def get_has_bookmark(cls, user: AbstractBaseUser | None):
        if user == None:
            return models.Value(False)
        return models.Exists(
            Bookmark.objects.filter(user=user, post_id=models.OuterRef("pk"))
        )

    @classmethod
    def get_has_repost(cls, user: AbstractBaseUser | None):
        if user == None:
            return models.Value(False)
        return models.Exists(
            Repost.objects.filter(user=user, post_id=models.OuterRef("pk"))
        )

    @classmethod
    def get_latest_relevant_repost(cls, user: AbstractBaseUser | None):
        if user == None:
            return models.Prefetch(
                "reposts",
                Repost.objects.filter(pk=0).order_by("-created_at")[:1],
                to_attr="relavant_repost",
            )

        return models.Prefetch(
            "reposts",
            Repost.objects.prefetch_related(
                models.Prefetch("user", User.concrete_queryset(user=user))
            )
            .filter(models.Q(user__followers__followed_by=user) | models.Q(user=user))
            .order_by("-created_at")[:1],
            to_attr="relavant_repost",
        )


class View(CommonModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="views")


class Favorite(CommonModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="favorites")


class Bookmark(CommonModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")


class Repost(CommonModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reposts")


class Mention(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="mentions")
    mentioned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mentioned"
    )
