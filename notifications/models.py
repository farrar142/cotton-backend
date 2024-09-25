from django.db import models

from commons.models import CommonModel

from posts.models import Repost, Favorite
from users.models import User


class NotificationBase(models.Model):
    user: models.ForeignKey[User]


# Create your models here.
class MentionedNotification(NotificationBase):
    class Meta:
        abstract = True

    mentioned_post = models.ForeignKey(
        Repost,
        on_delete=models.CASCADE,
        related_name="mentioned_notifications",
        null=True,
    )

    def _text(self):
        return


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
        return


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
        return


class Notification(
    MentionedNotification, RepostedNotification, FavoritedNotification, CommonModel
):
    is_checked = models.BooleanField(default=False)
