from typing import Self
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from commons.model_utils import make_property_field
from users.models import User


# Create your models here.
class MessageGroup(models.Model):
    is_direct_message = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    attendants: "models.ManyToManyField[User,Self]" = models.ManyToManyField(
        User, through="MessageAttendant", related_name="message_groups"
    )
    messages: "models.Manager[Message]"

    unreaded_messages = make_property_field(0)

    @classmethod
    def concrete_queryset(cls, user: AbstractBaseUser | None = None):
        if user and user.is_authenticated == False:
            user = None
        return cls.objects.prefetch_related(
            models.Prefetch("attendants", User.concrete_queryset(user))
        ).annotate(
            latest_message=cls.get_latest_message(),
            latest_message_user=cls.get_latest_message_user(),
            latest_message_nickname=cls.get_latest_message_nickname(),
            latest_message_created_at=cls.get_latest_message_created_at(),
            unreaded_messages=models.Count(
                Message.objects.annotate(
                    has_checked=Message.get_has_checked(user),
                )
                .filter(
                    has_checked=False,
                    group=models.OuterRef("pk"),
                )
                .values("group")
                .order_by("group")
                .annotate(count=models.Count("group"))
                .values("count")
            ),
        )

    @classmethod
    def get_latest_message(cls):
        return models.Subquery(
            Message.objects.filter(group=models.OuterRef("pk"))
            .order_by("-created_at")
            .values(
                "message",
            )[:1]
        )

    @classmethod
    def get_latest_message_user(cls):
        return models.Subquery(
            Message.objects.filter(group=models.OuterRef("pk"))
            .annotate(user=models.F("attendant__user"))
            .order_by("-created_at")
            .values(
                "user",
            )[:1]
        )

    @classmethod
    def get_latest_message_created_at(cls):
        return models.Subquery(
            Message.objects.filter(group=models.OuterRef("pk"))
            .annotate(user=models.F("attendant__user"))
            .order_by("-created_at")
            .values(
                "created_at",
            )[:1]
        )

    @classmethod
    def get_latest_message_nickname(cls):
        return models.Subquery(
            Message.objects.filter(group=models.OuterRef("pk"))
            .annotate(nickname=models.F("attendant__user__nickname"))
            .order_by("-created_at")
            .values(
                "nickname",
            )[:1]
        )


class MessageAttendant(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["group", "user"]),
            models.Index(fields=["user"]),
        ]

    group = models.ForeignKey(
        MessageGroup, on_delete=models.CASCADE, related_name="message_attendants"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="message_attendants"
    )
    messages: models.Manager["Message"]


class Message(models.Model):
    class Meta:
        indexes = [models.Index(fields=["group", "attendant", "id"])]

    created_at = models.DateTimeField(auto_now_add=True)

    group = models.ForeignKey(
        MessageGroup, on_delete=models.CASCADE, related_name="messages"
    )
    group_id: int
    attendant = models.ForeignKey(
        MessageAttendant, on_delete=models.CASCADE, related_name="messages"
    )
    message = models.TextField()
    identifier = models.CharField(max_length=63)

    user = make_property_field(0)
    nickname = make_property_field("")
    has_checked = make_property_field(False)

    checks: "models.Manager[MessageCheck]"

    @classmethod
    def get_has_checked(cls, user: AbstractBaseUser | None = None):
        if user and not user.is_authenticated:
            user = None
        if not user:
            return models.Value(False)
        return models.functions.Coalesce(
            models.Exists(
                MessageCheck.objects.filter(user=user, message=models.OuterRef("pk"))
            ),
            models.Value(False),
        )


class MessageCheck(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="checked_messages"
    )
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="checks"
    )
