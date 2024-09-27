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
        )

    bio = serializers.CharField(max_length=511, required=False)
    profile_image = ImageSerializer(required=False)


class UserSerializer(UserBaseSerializer):
    class Meta:
        model = User
        fields = UserBaseSerializer.Meta.fields + (
            "followers_count",
            "followings_count",
            "is_following_to",
            "is_followed_by",
            "is_mutual_follow",
            "is_registered",
            "registerd_at",
        )
        read_only_fields = ("registered_at",)

    registerd_at = serializers.DateTimeField(read_only=True)
    followers_count = serializers.IntegerField(required=False)
    followings_count = serializers.IntegerField(required=False)
    is_following_to = serializers.BooleanField(required=False)
    is_followed_by = serializers.BooleanField(required=False)
    is_mutual_follow = serializers.BooleanField(required=False)


class UserUpsertSerializer(BaseModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "bio", "profile_image", "nickname", "username")

    bio = serializers.CharField(max_length=511, required=False)
    profile_image = ImageSerializer(required=False)

    def create(self, validated_data):
        raise exceptions.MethodNotAllowed("post")

    def update(self, instance, validated_data):
        profile_image = validated_data.pop("profile_image", None)
        instance = super().update(instance, validated_data)
        if profile_image:
            serializer = ImageSerializer(
                data=self.initial_data["profile_image"]  # type:ignore
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            instance.profile_image = serializer.instance
            instance.save()
        return instance
