from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post, Repost, Bookmark, Favorite


@receiver(post_save, sender=Post)
def on_post_created(sender, instance: Post, **kwargs):
    return


@receiver(post_save, sender=Repost)
def on_repost_created(sender, instance: Post, **kwargs):
    return


@receiver(post_save, sender=Favorite)
def on_favorite_created(sender, instance: Post, **kwargs):
    return
