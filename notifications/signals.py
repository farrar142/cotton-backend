from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .serializers import NotificationSerializer
from users.consumers import UserConsumer


@receiver(post_save, sender=Notification)
def on_notification_created(
    sender: type[Notification], instance: Notification, created: bool, **kwargs
):
    if not created:
        return
    qs = Notification.concrete_queryset(user=instance.user).get(pk=instance.pk)
    serializer = NotificationSerializer(qs)
    if qs.user.pk == qs.from_user.pk:
        qs.delete()
        return
    UserConsumer.send_notification(instance.user_id, serializer.data)  # type:ignore
