from rest_framework import exceptions
from commons.paginations import TimelinePagination
from commons.viewsets import BaseViewset
from commons import permissions

from .serializers import NotificationSerializer
from .models import Notification, User


class NotificationViewSet(BaseViewset[Notification, User]):
    permission_classes = [permissions.AuthorizedOnly]
    queryset = Notification.concrete_queryset()
    read_only_serializer = NotificationSerializer
    upsert_serializer = NotificationSerializer
    pagination_class = TimelinePagination
    offset_field = "created_at"

    def get_queryset(self):
        self.queryset = Notification.concrete_queryset(self.request.user)
        return self.queryset.filter(user=self.request.user)

    @BaseViewset.action(methods=["POST"], detail=True, url_path="check")
    def check(self, *args, **kwargs):
        instance = self.get_object()
        instance.is_checked = True
        instance.save()
        return self.result_response(True, 201)
