from random import randint
from typing import TYPE_CHECKING

from django.db import models
from django.utils.timezone import localtime, timedelta

from commons.celery import shared_task
from users.models import User
from posts.text_builder.block_text_builder import BlockTextBuilder
from posts.serializers import PostSerializer

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
        _reply_to_users_post.delay(chatbot_id=bot_id, post_id=post.pk)


@shared_task(queue="window")
def _reply_to_users_post(chatbot_id: int, post_id: int):
    from posts.models import Post
    from posts.serializers import PostSerializer
    from posts.text_builder.block_text_builder import BlockTextBuilder
    from .rag import Rag, get_documents_from_posts

    chatbot = User.objects.get(pk=chatbot_id)
    post = Post.concrete_queryset(chatbot).get(pk=post_id)
    origins_data: list[Post] = []
    if post.origin:
        origins = (
            Post.concrete_queryset(chatbot)
            .filter(models.Q(origin=post.origin) | models.Q(pk=post.origin.pk))
            .exclude(pk=post_id)
            .order_by("-created_at")[:10]
        )
        origins_data = list(reversed(origins))

    origin_documents = get_documents_from_posts(origins_data, chatbot)
    # parent_documents = get_documents_from_posts([post], chatbot)
    post_docs = [*origin_documents]

    rag = Rag()
    content = rag.create_reply(
        chatbot=chatbot,
        user=post.user,
        query=post.text,
        post_docs=post_docs,
        collection_name="huffington",
    )
    # content = ai_chat(chatbot, data, origins_data)
    splitted = content.split("\n")
    builder = BlockTextBuilder()
    for text in splitted:
        builder.text(text).new_line()
    ser = PostSerializer(
        data=dict(
            text=builder.get_plain_text(),
            blocks=builder.get_json(),
            parent=post.pk,
            origin=post.origin.pk if post.origin else post.pk,
        ),
        user=chatbot,
    )
    ser.is_valid(raise_exception=True)
    ser.save()


from base.celery import app


@shared_task(queue="window")
def crawl_huffington_post():

    from .rag.combined import _crawl_huffinton_post

    _crawl_huffinton_post()


@shared_task(queue="window")
def chatbots_post_about_news():
    # 5분마다 한번 호출
    users = User.objects.filter(chatbots__isnull=False)
    for user in users:
        minute = randint(1, 10)
        if 5 < minute:
            continue
        _chatbot_post_about_news.apply_async(
            args=[user.pk], eta=localtime() + timedelta(minutes=minute)
        )


@shared_task(queue="window")
def _chatbot_post_about_news(user_id: int, collection_name: str = "huffington"):
    from .rag import Rag

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return
    rag = Rag()
    resp: str = rag.ask_llm(
        user,
        "Summarize just random one of today's news and make it like an sns post to your followers. \n Leave out the additional explanation and hashtags.\nWrite down your thoughts naturally too",
        collection_name=collection_name,
    )
    if "summary of today" in resp:
        return

    splitted = resp.split("\n")

    splitted = list(filter(lambda x: "summary of today" not in x, splitted))

    builder = BlockTextBuilder()
    for text in splitted:
        builder.text(text).new_line()

    ser = PostSerializer(
        data=dict(
            text=builder.get_plain_text(),
            blocks=builder.get_json(),
        ),
        user=user,
    )
    if not ser.is_valid():
        return
    ser.save()
