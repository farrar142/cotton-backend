from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import Follow, User


@receiver(m2m_changed, sender=Follow)
def on_following_created(sender, instance: User, **kwargs):
    from notifications.models import Notification

    pk_set: set[int] = kwargs.get("pk_set", set())
    action: str = kwargs.get("action", "")
    if action != "post_add":
        return
    followed_by = instance
    for pk in pk_set:
        following_user = User.objects.get(pk=pk)
        follow = Follow.objects.filter(
            followed_by=followed_by, following_to=following_user
        ).first()
        if not follow:
            continue

        notification = Notification()
        notification.user = following_user
        notification.from_user = followed_by
        notification.followed_user = follow
        notification.save()


# @receiver(post_save, sender=Follow)
# def on_following_created(sender, instance: Follow, **kwargs):

#     print(sender)
#     print(instance, type(instance))
#     print(kwargs)
#     noti = Notification()
#     noti.user = instance.following_to
#     noti.from_user = instance.followed_by
#     noti.followed_user = instance
#     noti.save()
