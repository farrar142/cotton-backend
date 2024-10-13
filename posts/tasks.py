from django.apps import apps
from django.utils.timezone import localtime, timedelta
from django.db import models
from commons.caches import LRUCache, TimeoutCache
from commons.celery import shared_task
from commons.lock import get_redis


@shared_task()
def on_post_created_task(post_id: int):
    from .models import Post
    from notifications.models import Notification
    from ai.tasks import create_ai_post

    if not (instance := Post.objects.filter(pk=post_id).first()):
        return
    flag = False
    noti = Notification()
    noti.from_user = instance.user
    if instance.parent:
        flag = True
        noti.user = instance.parent.user
        noti.replied_post = instance
    elif instance.quote:
        flag = True
        noti.user = instance.quote.user
        noti.quoted_post = instance
    if flag:
        noti.save()
    create_ai_post.delay(post_id=instance.pk)


def get_weights(instance):
    from .models import View, Favorite, Bookmark, Repost

    if isinstance(instance, Favorite):
        weights = 5
    elif isinstance(instance, Bookmark):
        weights = 2
    elif isinstance(instance, Repost):
        weights = 10
    return 1


@shared_task()
def create_child_model(model_path: str, child_str: str, instance_id: int, user_id: int):
    path_splitted = model_path.split(".")
    Model = apps.get_model(path_splitted[0], path_splitted[1])
    instance = Model.objects.filter(pk=instance_id).first()
    if not instance:
        return

    manager: models.Manager[models.Model] = getattr(instance, child_str)
    if manager.filter(user_id=user_id).exists():
        return

    instance = manager.create(user_id=user_id)
    weights = get_weights(instance)
    push_recommended_list.delay(instance_id, weights)


@shared_task()
def delete_child_models(
    model_path: str, child_str: str, instance_id: int, user_id: int
):
    path_splitted = model_path.split(".")
    Model = apps.get_model(path_splitted[0], path_splitted[1])
    instance = Model.objects.filter(pk=instance_id).first()
    if not instance:
        return
    manager: models.Manager[models.Model] = getattr(instance, child_str)
    if not (child := manager.filter(user_id=user_id).first()):
        return
    child.delete()
    weights = get_weights(instance)
    push_recommended_list.delay(instance_id, -weights)


@shared_task()
def push_recommended_list(post_id: int, weights):
    with TimeoutCache("post_recommended/v2") as cache:
        cache.add(post_id)


@shared_task()
def create_mentions_in_background(mentioned_to_id: int, post_id: int):
    from .models import Mention

    Mention.objects.create(mentioned_to_id=mentioned_to_id, post_id=post_id)


@shared_task()
def expire_post_recommended():
    with TimeoutCache("post_recommended/v2") as cache:
        cache.remove_out_dated(localtime() - timedelta(days=1))
