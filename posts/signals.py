from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post, Repost, Bookmark, Favorite, Mention


@receiver(post_save, sender=Post)
def on_post_created(sender, instance: Post, **kwargs):
    from .tasks import on_post_created_task

    on_post_created_task.delay(instance.pk)


@receiver(post_save, sender=Repost)
def on_repost_created(sender, instance: Repost, **kwargs):
    from notifications.models import Notification

    noti = Notification()
    noti.user = instance.post.user
    noti.from_user = instance.user
    noti.reposted_post = instance
    noti.save()


@receiver(post_save, sender=Favorite)
def on_favorite_created(sender, instance: Favorite, **kwargs):
    from notifications.models import Notification

    noti = Notification()
    noti.user = instance.post.user
    noti.from_user = instance.user
    noti.favorited_post = instance
    noti.save()


@receiver(post_save, sender=Mention)
def on_mention_created(sender, instance: Mention, **kwargs):
    from notifications.models import Notification

    noti = Notification()
    noti.user = instance.mentioned_to
    noti.from_user = instance.post.user
    noti.mentioned_post = instance
    noti.save()
