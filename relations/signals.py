from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Follow


@receiver(post_save, sender=Follow)
def on_following_created(sender, instance: Follow, **kwargs):
    pass
