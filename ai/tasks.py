from typing import TYPE_CHECKING
from django.db import models
from commons.celery import shared_task
from users.models import User

if TYPE_CHECKING:
    from posts.models import Post


def is_post_to_chatbot(post_id: int):
    from posts.models import Post

    is_child_post = models.Subquery(
        User.objects.filter(chatbots__user=models.OuterRef("parent__user")).values(
            "id"
        )[:1]
    )
    is_quoted_post = models.Subquery(
        User.objects.filter(chatbots__user=models.OuterRef("quote__user")).values("id")[
            :1
        ]
    )
    is_mentioned_post = models.Subquery(
        User.objects.filter(
            chatbots__user=models.OuterRef("mentions__mentioned_to")
        ).values("id")[:1]
    )
    post = (
        Post.objects.annotate(
            is_reply_to_ai=is_child_post,
            is_quote_to_ai=is_quoted_post,
            is_mentioned_post=is_mentioned_post,
        )
        .filter(pk=post_id)
        .filter(
            models.Q(is_reply_to_ai__isnull=False)
            | models.Q(is_quote_to_ai__isnull=False)
            | models.Q(is_mentioned_post__isnull=False)
        )
        .first()
    )
    return post


def parse_ai_users(post: "Post"):
    from posts.models import Post

    users: dict[int, Post] = dict()

    if post.is_reply_to_ai:
        users[post.is_reply_to_ai] = post
    if post.is_quote_to_ai:
        users[post.is_quote_to_ai] = post
    if post.is_mentioned_post:
        users[post.is_mentioned_post] = post
    return users
    # if post.quote:
    #     if post.quote.


@shared_task()
def create_ai_post(post_id: int):
    post = is_post_to_chatbot(post_id=post_id)
    if not post:
        return
    bots = parse_ai_users(post)
    for bot_id, post in bots.items():
        reply_to_users_post.delay(chatbot_id=bot_id, post_id=post.pk)


@shared_task()
def reply_to_users_post(chatbot_id: int, post_id: int):
    from posts.models import Post
    from posts.serializers import PostSerializer
    from posts.text_builder.block_text_builder import BlockTextBuilder
    from .ai_chat import ai_chat

    user = User.objects.get(pk=chatbot_id)
    post = Post.concrete_queryset(user).get(pk=post_id)
    origins_data = []
    if post.origin:
        origins = (
            Post.concrete_queryset(user)
            .filter(origin=post.origin)
            .order_by("-created_at")[:10]
        )
        print(origins)
        origins_data: list[dict] = PostSerializer(
            reversed(origins), many=True, user=user
        ).data  # type:ignore
    data: dict = PostSerializer(instance=post).data  # type:ignore
    content = ai_chat(user, data, origins_data)
    builder = BlockTextBuilder()
    builder.text(content)
    print(builder.get_plain_text())
    ser = PostSerializer(
        data=dict(
            text=builder.get_plain_text(),
            blocks=builder.get_json(),
            parent=post.pk,
            origin=post.origin.pk if post.origin else post.pk,
        ),
        user=user,
    )
    ser.is_valid(raise_exception=True)
    ser.save()
