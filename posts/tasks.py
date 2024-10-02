from django.apps import apps
from commons.celery import shared_task


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

    getattr(instance, child_str).create(user_id=user_id)


@shared_task()
def create_mentions_in_background(mentioned_to_id: int, post_id: int):
    from .models import Mention

    Mention.objects.create(mentioned_to_id=mentioned_to_id, post_id=post_id)
