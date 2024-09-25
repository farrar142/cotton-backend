from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import action

from commons.viewsets import GenericViewSet

from ..services import (
    AuthService,
    RefreshSerializer,
    SignupSerializer,
    SigninSerializer,
)


class AuthViewSet(GenericViewSet):
    authentication_classes = ()
    serializer_class = serializers.Serializer

    @action(methods=["POST"], detail=False, url_path="signin")
    def signin(self, r, *args, **kwargs):
        ser = SigninSerializer(data=r.data)
        ser.is_valid(raise_exception=True)

        data = AuthService.signin(**ser.data)  # type:ignore
        return Response(data)

    @action(methods=["POST"], detail=False, url_path="signup")
    def signup(self, r, *args, **kwargs):
        ser = SignupSerializer(data=r.data)
        ser.is_valid(raise_exception=True)
        user, data = AuthService.signup(**ser.data)  # type:ignore
        return Response(data, status=201)

    @action(methods=["POST"], detail=False, url_path="refresh")
    def refresh(self, r, *args, **kwargs):
        ser = RefreshSerializer(data=r.data)
        ser.is_valid(raise_exception=True)
        data = AuthService.refresh(ser.data["refresh"])  # type:ignore
        return Response(data)
