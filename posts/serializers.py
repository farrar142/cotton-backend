from commons.decorators import inject_user
from commons.serializers import BaseModelSerializer, serializers
from users.models import User
from users.serializers import UserSerializer

from .models import Post, Favorite, Bookmark, Repost, Mention, models


class MentionSerializer(BaseModelSerializer[Mention]):
    class Meta:
        model = Mention
        fields = ("id", "mentioned_to")

    mentioned_to = UserSerializer(queryset=User.objects.all())


class PlainTextTypeChoices(models.TextChoices):
    MENTION = "mention"
    TEXT = "text"


class MentionTextTypeChoices(models.TextChoices):
    MENTION = "mention"


class TextTypeChoices(models.TextChoices):
    TEXT = "text"


class PlainTextSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=PlainTextTypeChoices.choices, required=True)
    id = serializers.IntegerField(required=False)
    username = serializers.CharField(required=False)
    value = serializers.CharField(required=False)

    @property
    def data(self):
        if self.initial_data["type"] == MentionTextTypeChoices.MENTION:  # type:ignore
            ser = MentionTextSerializer(data=self.initial_data)
        else:
            ser = TextTextSerializer(data=self.initial_data)
        ser.is_valid(raise_exception=True)
        return ser.data


class MentionTextSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=MentionTextTypeChoices.choices, required=True
    )
    id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)
    username = serializers.CharField(required=True)
    value = serializers.CharField(required=True)


class TextTextSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=TextTypeChoices.choices, required=True)
    value = serializers.CharField(required=True)


@inject_user
class PostSerializer(BaseModelSerializer[Post]):
    class Meta:
        model = Post
        fields = (
            "id",
            "text",
            "blocks",
            "created_at",
            "has_bookmark",
            "has_repost",
            "has_favorite",
            "favorites_count",
            "mentions",
            "relavant_repost",
            "latest_date",
        )

    blocks = serializers.ListField(
        child=serializers.ListField(child=PlainTextSerializer())
    )
    mentions = MentionSerializer(many=True, required=False)

    has_favorite = serializers.BooleanField(read_only=True)
    has_bookmark = serializers.BooleanField(read_only=True)
    has_repost = serializers.BooleanField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    latest_date = serializers.DateTimeField(read_only=True)
    relavant_repost = serializers.SerializerMethodField()

    def get_relavant_repost(self, obj: Post):
        if getattr(obj, "relavant_repost", None):
            return UserSerializer(
                instance=obj.relavant_repost[0].user,  # type:ignore
                context=self.context,
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
