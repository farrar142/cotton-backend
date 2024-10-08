from rest_framework.request import Request

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token, RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.core.cache import cache


class CustomJWTAuthentication(JWTAuthentication):

    def authenticate(self, request: Request):
        access = request.META.get("HTTP_AUTHORIZATION")
        if data := self.get_cached_user(access):
            return data
        token = super().authenticate(request)
        cache.set(access, token, timeout=600)
        return token

    def get_cached_user(self, token: str):
        return cache.get(token, None)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user) -> RefreshToken:
        token = super().get_token(user)
        return token  # type:ignore
