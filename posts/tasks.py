from django.apps import apps
from django.utils.timezone import localtime, timedelta
from commons.caches import LRUCache, TimeoutCache
from commons.celery import shared_task
from commons.lock import get_redis


@shared_task()
def create_child_model(model_path: str, child_str: str, instance_id: int, user_id: int):
    path_splitted = model_path.split(".")
    Model = apps.get_model(path_splitted[0], path_splitted[1])
    instance = Model.objects.filter(pk=instance_id).first()
    if not instance:
        return
    manager = getattr(instance, child_str)
    if manager.filter(user_id=user_id).exists():
        return

    instance = getattr(instance, child_str).create(user_id=user_id)
    from .models import View, Favorite, Bookmark, Repost

    weights = 1
    if isinstance(Favorite, instance):
        weights = 5
    elif isinstance(Bookmark, instance):
        weights = 2
    elif isinstance(Repost, instance):
        weights = 10
    push_recommended_list.delay(instance_id, weights)


@shared_task()
def push_recommended_list(post_id: int, weights):
    with TimeoutCache("post_recommended") as cache:
        cache.add(post_id)


@shared_task()
def create_mentions_in_background(mentioned_to_id: int, post_id: int):
    from .models import Mention

    Mention.objects.create(mentioned_to_id=mentioned_to_id, post_id=post_id)


@shared_task()
def expire_post_recommended():
    with TimeoutCache("post_recommended") as cache:
        cache.remove_out_dated(localtime() - timedelta(days=1))
