from rest_framework import exceptions

from commons import permissions
from commons.viewsets import BaseViewset
from commons.paginations import TimelinePagination, CursorPagination

from users.models import User

from .models import Message, MessageGroup, MessageAttendant
from .serializers import (
    MessageGroupSerializer,
    MessageSerializer,
    UserSerializer,
    serializers,
)
from .services import MessageService


class MessageGroupViewset(BaseViewset[MessageGroup, User]):
    permission_classes = [permissions.AuthorizedOnly]
    pagination_class = TimelinePagination
    offset_field = "latest_message_created_at"
    queryset = MessageGroup.concrete_queryset()

    read_only_serializer = MessageGroupSerializer
    upsert_serializer = MessageGroupSerializer

    action = BaseViewset.action

    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("POST")

    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PUT")

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("PATCH")

    def destroy(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("DELETE")

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            raise
        return MessageService.get_message_groups(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        print(request.user)
        return super().retrieve(request, *args, **kwargs)

    @action(methods=["POST"], detail=False, url_path="create")
    def create_group(self, *args, **kwargs):
        class CreateSerializer(serializers.Serializer):
            users = UserSerializer(many=True, queryset=User.objects.all())
            title = serializers.CharField(max_length=255, default="", required=False)

        serializer = CreateSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data["title"]  # type:ignore
        users: list[User] = [
            self.request.user,
            *serializer.validated_data["users"],  # type:ignore
        ]
        pk_flattened = set(map(lambda x: x.pk, users))
        if len(set(pk_flattened)) == 1:
            raise exceptions.ValidationError(
                detail=dict(user=["자신에게 대화를 보낼 수 없습니다."])
            )
        service = MessageService.create(
            *users, is_direct_message=len(pk_flattened) == 2, title=title
        )
        self.get_object = lambda: service.group
        response = self.retrieve(*args, **kwargs)
        response.status_code = 201
        return response

    @action(methods=["GET"], detail=False, url_path="has_unreaded_messages")
    def get_has_unreaded_messages(self, *args, **kwargs):
        unreaded = MessageService.get_unreaded_message(self.request.user)
        return self.Response(dict(count=unreaded.count()))

    @action(methods=["POST"], detail=True, url_path="check_as_readed")
    def post_check_messages(self, *args, **kwargs):
        service = MessageService(self.get_object())
        service.check_message(self.request.user)
        return self.result_response(True, 201)

    @action(methods=["GET"], detail=True, url_path="messages")
    def get_messages(self, *args, **kwargs):
        group = self.get_object()
        service = MessageService(group)
        self.get_queryset = lambda: service.get_messages(
            self.request.user
        )  # type:ignore
        self.get_serializer_class = lambda: MessageSerializer
        self.pagination_class = CursorPagination
        self.pagination_class.page_size = 20
        return self.list(*args)

    @action(methods=["POST"], detail=True, url_path="send_message")
    def send_message(self, *args, **kwargs):
        class Serializer(serializers.Serializer):
            message = serializers.CharField()
            identifier = serializers.CharField(required=False)

        s = Serializer(data=self.request.data)
        s.is_valid(raise_exception=True)
        message, identifier = s.data["message"], s.data.get("identifier")  # type:ignore
        service = MessageService(self.get_object())
        service.send_message(self.request.user, message, identifier)
        return self.result_response(True, 201)
