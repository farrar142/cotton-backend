from functools import partial, wraps
from typing import Iterable, Self, TYPE_CHECKING
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.db import models

from commons.model_utils import make_property_field
from images.models import Image


class UserAbstract(AbstractBaseUser, PermissionsMixin):
    class Meta:
        abstract = True

    default_manager = UserManager[Self]()
    username = models.CharField(max_length=30, unique=True)
    nickname = models.CharField(max_length=255, default="")
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    USERNAME_FIELD = "email"

    @classmethod
    @property
    def objects(cls):
        return cls.default_manager

    def __str__(self):
        return self.username

    @classmethod
    def concrete_queryset(cls, *args, **kwargs):
        return cls.objects.all()


if TYPE_CHECKING:
    from relations.models import Follow
    from chats.models import MessageGroup, MessageAttendant


class User(UserAbstract):
    is_registered = models.BooleanField(default=False)
    registered_at = models.DateTimeField(null=True)
    bio = models.CharField(max_length=511, default="")
    header_image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, related_name="header_users"
    )
    profile_image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, related_name="profile_users"
    )

    followings: "models.ManyToManyField[Follow,Self]" = models.ManyToManyField(
        "User",
        through="relations.Follow",
        through_fields=("followed_by", "following_to"),
    )
    followers: models.Manager["User"]
    message_groups: "models.Manager[MessageGroup]"
    message_attendants: "models.Manager[MessageAttendant]"

    followings_count = make_property_field(False)
    followers_count = make_property_field(False)

    is_following_to = make_property_field(False)
    is_followed_by = make_property_field(False)
    is_mutual_follow = make_property_field(False)

    following_at = make_property_field(None)
    followed_by_at = make_property_field(None)

    @classmethod
    def get_following_model(cls) -> "Follow":
        from pprint import pprint as pp

        return cls.followings.through  # type:ignore

    @classmethod
    def concrete_queryset(cls, user: AbstractBaseUser | None = None, *args, **kwargs):
        if user and not user.is_authenticated:
            user = None

        return (
            super()
            .concrete_queryset(*args, **kwargs)
            .select_related("profile_image")
            .annotate(
                followers_count=cls.get_followers_count(),
                followings_count=cls.get_followings_count(),
                is_following_to=cls.get_is_following_to(user=user),
                is_followed_by=cls.get_is_followed_by(user=user),
                is_mutual_follow=cls.get_is_mutual_follow(),
                following_at=cls.get_following_at(user=user),
                followed_by_at=cls.get_followed_by_at(user=user),
            )
        )

    @classmethod
    def get_followers_count(cls):
        Follow = cls.get_following_model()
        return models.Subquery(
            Follow.objects.filter(following_to=models.OuterRef("pk"))
            .values("following_to")
            .order_by("following_to")
            .annotate(count=models.Count("pk"))
            .values("count")
        )

    @classmethod
    def get_followings_count(cls):
        Follow = cls.get_following_model()
        return models.Subquery(
            Follow.objects.filter(followed_by=models.OuterRef("pk"))
            .values("followed_by")
            .order_by("followed_by")
            .annotate(count=models.Count("pk"))
            .values("count")
        )

    @classmethod
    def get_following_at(cls, user: AbstractBaseUser | None):
        Follow = cls.get_following_model()
        if not user:
            return models.ExpressionWrapper(models.Value(None), models.DateTimeField())
        return models.ExpressionWrapper(
            models.Subquery(
                Follow.objects.filter(
                    following_to=models.OuterRef("pk"), followed_by=user
                ).values("created_at"),
            ),
            output_field=models.DateTimeField(),
        )

    @classmethod
    def get_followed_by_at(cls, user: AbstractBaseUser | None):
        Follow = cls.get_following_model()
        if not user:
            return models.ExpressionWrapper(models.Value(None), models.DateTimeField())
        return models.ExpressionWrapper(
            models.Subquery(
                Follow.objects.filter(
                    followed_by=models.OuterRef("pk"),
                    following_to=user,
                ).values("created_at"),
            ),
            output_field=models.DateTimeField(),
        )

    @classmethod
    def get_is_following_to(cls, user: AbstractBaseUser | None):
        Follow = cls.get_following_model()

        if not user:
            return models.Value(False)

        return models.Exists(
            Follow.objects.filter(followed_by=user, following_to=models.OuterRef("pk"))
        )

    @classmethod
    def get_is_followed_by(cls, user: AbstractBaseUser | None):
        Follow = cls.get_following_model()
        if not user:
            return models.Value(False)

        return models.Exists(
            Follow.objects.filter(
                followed_by=models.OuterRef("pk"),
                following_to=user,
            )
        )

    @classmethod
    def get_is_mutual_follow(cls):
        return models.Q(is_following_to=models.Value(True)) & models.Q(
            is_followed_by=models.Value(True)
        )

    def save(self, *args, **kwargs) -> None:
        return super().save(*args, **kwargs)
