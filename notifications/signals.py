from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification
from chats.consumers import UserConsumer


@receiver(post_save, sender=Notification)
def on_notification_created(
    sender: type[Notification], instance: Notification, **kwargs
):
    UserConsumer.send_notification(instance.user_id, dict(id=instance.pk))
