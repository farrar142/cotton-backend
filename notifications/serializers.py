from commons.serializers import BaseModelSerializer, serializers
from users.serializers import UserSerializer

from posts.serializers import RepostSerializer, FavoriteSerializer, MentionSerializer

from .models import Notification, Post, Repost, User, Favorite, Follow


class NotificationSerializer(BaseModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "user",
            "from_user",
            "mentioned_post",
            "reposted_post",
            "favorited_post",
            "quoted_post",
            "followed_user",
            "replied_post",
            "created_at",
            "is_checked",
            "text",
        )

    user = UserSerializer(queryset=User.objects.all())
    from_user = UserSerializer(queryset=User.objects.all())
    mentioned_post = MentionSerializer()
    reposted_post = RepostSerializer()
    favorited_post = FavoriteSerializer()
    quoted_post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    followed_user = serializers.PrimaryKeyRelatedField(queryset=Follow.objects.all())
    replied_post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())
    text = serializers.CharField()
