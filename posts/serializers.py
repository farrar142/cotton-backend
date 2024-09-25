from commons.decorators import inject_user
from commons.serializers import BaseModelSerializer, serializers
from users.models import User
from users.serializers import UserSerializer

from .models import Post, Favorite, Bookmark, Repost, Mention


class MentionSerializer(BaseModelSerializer[Mention]):
    class Meta:
        model = Mention
        fields = ("id", "mentioned_to")

    mentioned_to = UserSerializer(queryset=User.objects.all())


@inject_user
class PostSerializer(BaseModelSerializer[Post]):
    class Meta:
        model = Post
        fields = (
            "id",
            "text",
            "created_at",
            "has_bookmark",
            "has_repost",
            "has_favorite",
            "favorites_count",
            "mentions",
            "relavant_repost",
            "latest_date",
        )

    mentions = MentionSerializer(many=True, required=False)

    has_favorite = serializers.BooleanField(read_only=True)
    has_bookmark = serializers.BooleanField(read_only=True)
    has_repost = serializers.BooleanField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    latest_date = serializers.DateTimeField(read_only=True)
    relavant_repost = serializers.SerializerMethodField()

    def get_relavant_repost(self, obj: Post):
        print(obj.relavant_repost)
        if obj.relavant_repost:
            return UserSerializer(
                instance=obj.relavant_repost[0].user, context=self.context
            ).data
        return None

    def create(self, validated_data):
        mentions = validated_data.pop("mentions", [])
        instance: Post = super().create(validated_data)
        if instance:
            instance.mentions.bulk_create(
                [
                    Mention(mentioned_to=mention["mentioned_to"], post=instance)
                    for mention in mentions
                ]
            )
        return instance


@inject_user
class FavoriteSerializer(BaseModelSerializer[Favorite]):
    class Meta:
        model = Favorite
        fields = ("id", "post", "created_at")


@inject_user
class BookmarkSerializer(BaseModelSerializer[Bookmark]):
    class Meta:
        model = Bookmark
        fields = ("id", "post", "created_at")


@inject_user
class RepostSerializer(BaseModelSerializer[Repost]):
    class Meta:
        model = Repost
        fields = ("id", "post", "created_at")
