from uuid import uuid4
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction, models
from rest_framework import exceptions

from commons.lock import with_lock

from .models import User, MessageGroup, MessageAttendant, Message, MessageCheck, models
from .tasks import send_message_by_ws_to_group


class MessageService:
    @classmethod
    @transaction.atomic
    def create(cls, *users: User, is_direct_message: bool = True, title: str = ""):
        pk_flattened = map(lambda u: u.pk, users)
        key = "message-create=" + ":".join(sorted(map(str, pk_flattened)))
        with with_lock(key):
            if is_direct_message:
                if group := cls.get_direct_message_group(*users):
                    return cls(group)

            group = MessageGroup.objects.create(
                is_direct_message=is_direct_message, title=title
            )
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
        instance.checks.create(user=user)
        send_message_by_ws_to_group.delay(instance.pk)
        return instance

    def get_messages(self, user: User):
        return self.group.messages.annotate(
            user=models.F("attendant__user"),
            nickname=models.F("attendant__user__nickname"),
            has_checked=Message.get_has_checked(user),
        ).all()

    @classmethod
    def get_unreaded_message(cls, user: AbstractBaseUser):
        return Message.objects.annotate(
            user=models.F("attendant__user"),
            nickname=models.F("attendant__user__nickname"),
            has_checked=Message.get_has_checked(user),
        ).filter(
            has_checked=False,
            group__attendants=user,
        )

    def check_message(self, user: AbstractBaseUser):
        messages = self.__class__.get_unreaded_message(user).filter(group=self.group)
        message_checks = [
            MessageCheck(user=user, message=message) for message in messages
        ]
        MessageCheck.objects.bulk_create(message_checks)
