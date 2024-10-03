from commons.serializers import BaseModelSerializer, serializers
from users.serializers import UserSerializer
from .models import MessageGroup, Message, User


class MessageGroupSerializer(BaseModelSerializer[MessageGroup]):
    class Meta:
        model = MessageGroup
        fields = (
            "id",
            "is_direct_message",
            "attendants",
            "created_at",
            "latest_message",
            "latest_message_user",
            "latest_message_nickname",
            "latest_message_created_at",
        )

    attendants = UserSerializer(many=True)
    latest_message = serializers.CharField(required=False)
    latest_message_nickname = serializers.CharField(required=False)
    latest_message_user = serializers.IntegerField(required=False)
    latest_message_created_at = serializers.DateTimeField(required=False)


class MessageSerializer(BaseModelSerializer[Message]):
    class Meta:
        model = Message
        fields = ("user", "id", "created_at", "message", "identifier")

    user = serializers.IntegerField()
