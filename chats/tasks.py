from commons.celery import shared_task

from users.models import User
from users.consumers import UserConsumer

from .serializers import MessageSerializer
from .models import MessageGroup, Message, MessageAttendant, MessageCheck, models


@shared_task()
def create_mssage(group_id: int, user_id: int, message: str, identifier: str):
    if not (
        attendant := MessageAttendant.objects.filter(
            group_id=group_id, user_id=user_id
        ).first()
    ):
        return
    instance = attendant.messages.create(
        grup_id=group_id, message=message, identifier=identifier
    )
    instance.checks.create(user_id=user_id)
    send_message_by_ws_to_group.delay(instance.pk)


@shared_task()
def check_messages(group_id: int, user_id: int):
    from .services import MessageService

    group = MessageGroup.objects.filter(pk=group_id).first()
    user = User.objects.filter(pk=user_id).first()
    if not group or not user:
        return
    service = MessageService(group)
    messages = service.__class__.get_unreaded_message(user).filter(group=group)

    message_checks = [MessageCheck(user=user, message=message) for message in messages]
    MessageCheck.objects.bulk_create(message_checks)


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
        UserConsumer.send_group_changed_message(user.pk, group.pk)  # type:ignore


@shared_task()
def delete_no_message_group(group_id):
    if not (group := MessageGroup.objects.filter(pk=group_id).first()):
        return
    if group.messages.all().exists():
        return
    group.delete()
