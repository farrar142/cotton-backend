from uuid import uuid4
from django.db import transaction, models

from commons.lock import with_lock

from .models import User, MessageGroup, MessageAttendant, Message, models
from .tasks import send_message_to_ws


class MessageService:
    @classmethod
    @transaction.atomic
    def create(cls, *users: User, is_direct_message: bool = True):
        key = "message-create=" + ":".join(sorted(map(str, map(lambda u: u.pk, users))))
        with with_lock(key):
            if is_direct_message:
                if group := cls.get_direct_message_group(*users):
                    return cls(group)

            group = MessageGroup.objects.create(is_direct_message=is_direct_message)
            group.attendants.add(*users)
            return cls(group)

    @classmethod
    def get_direct_message_group(cls, *users: User):
        group_values = (
            MessageAttendant.objects.filter(
                user__in=users, group__is_direct_message=True
            )
            .values("group")
            .order_by("group")
            .annotate(group_count=models.Count("pk"))
            .values("group_count", "group")
            .filter(group_count=2)
        )
        if 1 < len(group_values):
            raise Exception("그룹수가 많은데")
        if group_value := group_values.first():
            return MessageGroup.objects.get(pk=group_value.get("group"))
        return None

    @classmethod
    def get_message_groups(cls, user: User):
        return MessageGroup.concrete_queryset(user).filter(attendants=user)

    def __init__(self, group: MessageGroup):
        self.group = group

    def send_message(self, user: User, message: str, identifier: str | None = None):
        if identifier == None:
            identifier = str(uuid4())
        attendant = MessageAttendant.objects.get(group=self.group, user=user)
        instance = attendant.messages.create(
            group=self.group, message=message, identifier=identifier
        )
        send_message_to_ws.delay(instance.pk)
        return instance

    def get_messages(self):
        return self.group.messages.annotate(user=models.F("attendant__user")).all()
