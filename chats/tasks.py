from commons.celery import shared_task

from .consumers import UserConsumer
from .serializers import MessageSerializer
from .models import MessageGroup, Message, models


@shared_task()
def send_message_by_ws_to_group(message_id: int):
    if not (
        message := Message.objects.annotate(
            user=models.F("attendant__user"),
            nickname=models.F("attendant__user__nickname"),
            has_checked=models.Value(False),
        )
        .prefetch_related(
            models.Prefetch(
                "group", MessageGroup.objects.prefetch_related("attendants")
            )
        )
        .filter(pk=message_id)
        .first()
    ):
        return
    data = MessageSerializer(message).data
    for user in message.group.attendants.all():
        UserConsumer.send_message(user.pk, data)  # type:ignore


@shared_task()
def send_group_state_changed_to_users(group_id: int):
    group = MessageGroup.objects.filter(pk=group_id).first()
    if not group:
        return
    for user in group.attendants.all():
        UserConsumer.send_group_message(user.pk, group.pk)  # type:ignore


@shared_task()
def delete_no_message_group(group_id):
    if not (group := MessageGroup.objects.filter(pk=group_id).first()):
        return
    if group.messages.all().exists():
        return
    group.delete()
