from typing import TYPE_CHECKING, Callable, Self, TypeVar
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from commons.models import CommonModel

from posts.models import Post, Repost, Favorite, Mention
from users.models import User
from relations.models import Follow

if TYPE_CHECKING:
    NB = TypeVar("NB", bound="NotificationBase")


class NotificationBase(models.Model):
    class Meta:
        abstract = True

    user: models.ForeignKey[User]
    from_user: models.ForeignKey[User]

    def _text(self) -> str:
        return ""

    @property
    def text(self):
        return self._text()


# Create your models here.
class MentionedNotification(NotificationBase):
    class Meta:
        abstract = True

    mentioned_post = models.ForeignKey(
        Mention,
        on_delete=models.CASCADE,
        related_name="mentioned_notifications",
        null=True,
    )

    def _text(self):
        if not self.mentioned_post:
            return super()._text()
        return "{{nickname}}님이 회원님을 언급했습니다"


class RepostedNotification(NotificationBase):
    class Meta:
        abstract = True

    reposted_post = models.ForeignKey(
        Repost,
        on_delete=models.CASCADE,
        related_name="reposted_notifications",
        null=True,
    )

    def _text(self):
        if not self.reposted_post:
            return super()._text()
        return "{{nickname}}님이 회원님의 게시글을 코트닝했습니다"


class FavoritedNotification(NotificationBase):
    class Meta:
        abstract = True

    favorited_post = models.ForeignKey(
        Favorite,
        on_delete=models.CASCADE,
        related_name="favorited_notifications",
        null=True,
    )

    def _text(self):
        if not self.favorited_post:
            return super()._text()
        return "{{nickname}}님이 회원님의 게시글을 좋아합니다"


class RepliedNotification(NotificationBase):
    class Meta:
        abstract = True

    replied_post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="replied_notifications",
        null=True,
    )

    def _text(self):
        if not self.replied_post:
            return super()._text()
        return "{{nickname}}님이 회원님의 게시글에 답글을 남겼습니다"


class QuotedNotification(NotificationBase):
    class Meta:
        abstract = True

    quoted_post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="quoted_notifications",
        null=True,
    )

    def _text(self):
        if not self.quoted_post:
            return super()._text()
        return "{{nickname}}님이 회원님의 게시글을 인용했습니다."


class FollowedNotification(NotificationBase):
    class Meta:
        abstract = True

    followed_user = models.ForeignKey(
        Follow,
        on_delete=models.CASCADE,
        related_name="followed_notifications",
        null=True,
    )

    def _text(self):
        if not self.followed_user:
            return super()._text()
        return "{{nickname}}님이 회원님을 팔로우했습니다."


class Notification(
    MentionedNotification,
    RepostedNotification,
    FavoritedNotification,
    RepliedNotification,
    QuotedNotification,
    FollowedNotification,
    CommonModel,
):
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_notifications"
    )

    is_checked = models.BooleanField(default=False)

    @classmethod
    def concrete_queryset(cls, user: AbstractBaseUser | None = None, *args, **kwargs):
        if user and not user.is_authenticated:
            user = None
        return (
            super()
            .concrete_queryset(user, *args, **kwargs)
            .select_related("favorited_post", "reposted_post", "mentioned_post")
        )
