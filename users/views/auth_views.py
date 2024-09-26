from rest_framework import serializers, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action

from commons import permissions
from commons.viewsets import GenericViewSet
from commons.authentication import CustomJWTAuthentication

from ..services import (
    AuthService,
    RefreshSerializer,
    SignupSerializer,
    SigninSerializer,
    CodeKeySerializer,
    TokenSerializer,
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
        AuthService(user).send_register_email()
        return Response(data, status=201)

    @action(
        methods=["POST"],
        detail=False,
        url_path="send_register_email",
    )
    def send_register(self, *args, **kwargs):
        ser = TokenSerializer(data=self.request.data)  # type:ignore
        ser.is_valid(raise_exception=True)
        auth = CustomJWTAuthentication()
        validated_token = auth.get_validated_token(
            ser.data.get("access", "").encode()  # type:ignore
        )
        user = auth.get_user(validated_token)

        service = AuthService(user)  # type:ignore
        service.send_register_email()
        return Response({"is_success": True})

    @action(methods=["POST"], detail=False, url_path="register")
    def register(self, *args, **kwargs):
        serializer = CodeKeySerializer(data=self.request.data)  # type:ignore
        serializer.is_valid(raise_exception=True)
        data = AuthService.register_user(**serializer.data)  # type:ignore
        return Response(data)

    @action(methods=["POST"], detail=False, url_path="refresh")
    def refresh(self, r, *args, **kwargs):
        ser = RefreshSerializer(data=r.data)
        ser.is_valid(raise_exception=True)
        data = AuthService.refresh(ser.data["refresh"])  # type:ignore
        return Response(data)
