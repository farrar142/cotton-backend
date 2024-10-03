from commons.celery import shared_task

from .consumers import ChatConsumer
from .serializers import MessageSerializer
from .models import MessageGroup, Message, models


@shared_task()
def send_message_to_ws(message_id: int):
    if not (
        message := Message.objects.annotate(user=models.F("attendant__user"))
        .filter(pk=message_id)
        .first()
    ):
        return
    data = MessageSerializer(message).data
    ChatConsumer.send_message(message.group_id, data)  # type:ignore


@shared_task()
def delete_no_message_group(group_id):
    if not (group := MessageGroup.objects.filter(pk=group_id).first()):
        return
    if group.messages.all().exists():
        return
    group.delete()
