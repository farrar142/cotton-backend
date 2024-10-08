from commons.decorators import inject_user
from commons.serializers import BaseModelSerializer, serializers
from images.serializers import ImageSerializer
from users.models import User
from users.serializers import UserSerializer

from .models import Post, Favorite, Bookmark, Repost, Mention, View, models


class MentionSerializer(BaseModelSerializer[Mention]):
    class Meta:
        model = Mention
        fields = ("id", "mentioned_to", "post")

    mentioned_to = UserSerializer(queryset=User.objects.all())
    post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), required=False
    )


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
            "has_view",
            "has_bookmark",
            "has_repost",
            "has_favorite",
            "has_quote",
            "views_count",
            "favorites_count",
            "reposts_count",
            "quotes_count",
            "mentions",
            "relavant_repost",
            "latest_date",
            "images",
            "parent",
            "origin",
            "quote",
            "replies_count",
            "depth",
            "reply_row_number_desc",
        )

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), required=False
    )
    origin = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), required=False
    )
    quote = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), required=False
    )
    blocks = serializers.ListField(
        child=serializers.ListField(child=PlainTextSerializer())
    )
    mentions = MentionSerializer(many=True, required=False)
    images = ImageSerializer(many=True, required=False)

    has_view = serializers.BooleanField(read_only=True)
    has_favorite = serializers.BooleanField(read_only=True)
    has_bookmark = serializers.BooleanField(read_only=True)
    has_repost = serializers.BooleanField(read_only=True)
    has_quote = serializers.BooleanField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    reposts_count = serializers.IntegerField(read_only=True)
    quotes_count = serializers.IntegerField(read_only=True)
    latest_date = serializers.DateTimeField(read_only=True)
    relavant_repost = serializers.SerializerMethodField()
    reply_row_number_desc = serializers.IntegerField(read_only=True)

    def get_relavant_repost(self, obj: Post):
        if getattr(obj, "relavant_repost", None):
            return UserSerializer(
                instance=obj.relavant_repost[0].user,  # type:ignore
                context=self.context,
            ).data
        return None

    def create(self, validated_data):
        mentions = validated_data.pop("mentions", [])
        images = validated_data.pop("images", [])
        parent = validated_data.get("parent", None)
        if parent:
            validated_data["depth"] = parent.depth + 1
        instance: Post = super().create(validated_data)
        if mentions:
            from .tasks import create_mentions_in_background

            for mention in mentions:
                create_mentions_in_background.delay(
                    mentioned_to_id=mention["mentioned_to"].pk, post_id=instance.pk
                )
        if images:
            ser = ImageSerializer(
                data=self.initial_data["images"], many=True  # type:ignore
            )
            ser.is_valid(raise_exception=True)
            ser.save()
            instance.images.add(*ser.instance)  # type:ignore
        return instance


@inject_user
class ViewSerializer(BaseModelSerializer[View]):
    class Meta:
        model = View
        fields = ("id", "post", "created_at")


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
