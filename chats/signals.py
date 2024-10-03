from datetime import timedelta
import time
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PERIOD_CHOICES

from .models import MessageGroup
from .tasks import delete_no_message_group


@receiver(post_save, sender=MessageGroup)
def on_message_group_created(
    sender: type[MessageGroup], instance: MessageGroup, created: bool, **kwargs
):
    if not created:
        return
    delete_no_message_group.apply_async(
        kwargs=dict(group_id=instance.pk), eta=timezone.localtime() + timedelta(hours=1)
    )
