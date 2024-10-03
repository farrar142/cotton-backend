from commons.celery import shared_task

from .consumers import ChatConsumer
from .serializers import MessageSerializer
from .models import Message, models


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
