import os
from random import choice
import threading

from django.utils import autoreload

from django.core.management.base import BaseCommand, CommandError
from users.models import User, models
from ...models import ChatBot
from ...tasks import crawl_news, _chatbot_post_about_news


class Command(BaseCommand):
    help = "ai posts news"

    def handle(self, tests=[], *args, **options):
        # 5분마다 한번 호출
        users = User.objects.prefetch_related(
            models.Prefetch(
                "chatbots",
                ChatBot.objects.prefetch_related("news_subscriptions").all(),
            )
        ).filter(chatbots__isnull=False)

        for user in users:
            if not (chatbot := user.chatbots):
                continue
            if not (subscriptions := chatbot.news_subscriptions.all()):
                continue
            news = choice(subscriptions)
            _chatbot_post_about_news.delay(
                user.pk, collection_name=news.collection_name
            )
