from typing import Any, Callable
from rest_framework import exceptions
from commons.serializers import BaseModelSerializer, serializers
from images.serializers import ImageSerializer
from .models import User


class UserBaseSerializer(BaseModelSerializer[User]):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "nickname",
            "email",
            "is_staff",
            "registered_at",
            "bio",
            "profile_image",
            "header_image",
        )

    bio = serializers.CharField(max_length=511, required=False)
    header_image = ImageSerializer(required=False)
    profile_image = ImageSerializer(required=False)


class UserSerializer(UserBaseSerializer):
    class Meta:
        model = User
        fields = UserBaseSerializer.Meta.fields + (
            "followers_count",
            "followings_count",
            "is_following_to",
            "is_followed_by",
            "following_at",
            "followed_by_at",
            "is_mutual_follow",
            "is_registered",
            "registerd_at",
            "name",
            "is_chat_bot",
            "is_protected",
        )
        read_only_fields = ("registered_at",)

    registerd_at = serializers.DateTimeField(read_only=True)
    followers_count = serializers.IntegerField(required=False)
    followings_count = serializers.IntegerField(required=False)
    is_following_to = serializers.BooleanField(required=False)
    is_followed_by = serializers.BooleanField(required=False)
    following_at = serializers.DateTimeField(required=False)
    followed_by_at = serializers.DateTimeField(required=False)
    is_mutual_follow = serializers.BooleanField(required=False)
    is_chat_bot = serializers.BooleanField(required=False)
    name = serializers.SerializerMethodField()

    def get_name(self, obj: User):
        return obj.username


class UserUpsertSerializer(BaseModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "bio", "profile_image", "header_image", "nickname", "username")

    username = serializers.CharField(
        max_length=64, required=False, allow_null=True, allow_blank=True
    )
    bio = serializers.CharField(
        max_length=511, required=False, allow_null=True, allow_blank=True
    )
    header_image = ImageSerializer(required=False, allow_null=True)
    profile_image = ImageSerializer(required=False, allow_null=True)

    def create(self, validated_data):
        raise exceptions.MethodNotAllowed("post")

    def update(self, instance, validated_data):
        validated_data.pop("header_image", None)
        validated_data.pop("profile_image", None)
        instance = super().update(instance, validated_data)
        self.create_image(instance, "profile_image")
        self.create_image(instance, "header_image")

        return instance

    def create_image(self, instance: User, key: str):
        image = self.initial_data.get(key)  # type:ignore
        if not image:
            return
        serializer = ImageSerializer(data=image)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        setattr(instance, key, serializer.instance)
        instance.save()
