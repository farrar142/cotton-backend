from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Follow


@receiver(post_save, sender=Follow)
def on_following_created(sender, instance: Follow, **kwargs):
    from notifications.models import Notification

    noti = Notification()
    noti.user = instance.following_to
    noti.from_user = instance.followed_by
    noti.followed_user = instance
    noti.save()
