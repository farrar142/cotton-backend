from datetime import datetime, timedelta
import time
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PERIOD_CHOICES

from .models import User
from .tasks import delete_unregistered_user


@receiver(post_save, sender=User)
def on_user_created(sender: type[User], instance: User, created: bool, **kwargs):
    if not created:
        return
    delete_unregistered_user.apply_async(
        kwargs=dict(user_id=instance.pk), eta=datetime.now() + timedelta(hours=1)
    )
