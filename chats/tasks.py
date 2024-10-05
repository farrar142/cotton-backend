from commons.celery import shared_task

from .consumers import ChatConsumer, UserConsumer
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
        send_message_by_ws_to_user(user.pk, data)  # type:ignore
    # ChatConsumer.send_message(message.group_id, data)  # type:ignore


@shared_task()
def send_message_by_ws_to_user(user_id: int, message: dict):
    UserConsumer.send_message(user_id, message)


@shared_task()
def delete_no_message_group(group_id):
    if not (group := MessageGroup.objects.filter(pk=group_id).first()):
        return
    if group.messages.all().exists():
        return
    group.delete()
