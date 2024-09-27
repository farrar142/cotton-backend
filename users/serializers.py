from commons.serializers import BaseModelSerializer, serializers
from .models import User


class UserBaseSerializer(BaseModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "username", "nickname", "email", "is_staff")


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
        )

    followers_count = serializers.IntegerField(required=False)
    followings_count = serializers.IntegerField(required=False)
    is_following_to = serializers.BooleanField(required=False)
    is_followed_by = serializers.BooleanField(required=False)
    is_mutual_follow = serializers.BooleanField(required=False)
