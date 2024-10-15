import os
from random import choice
import threading

from django.utils import autoreload

from django.core.management.base import BaseCommand, CommandError
from users.models import User, models
from ...models import NewsCrawler
from ...rag import chroma


class Command(BaseCommand):
    help = "ai posts news"

    def handle(self, tests=[], *args, **options):
        # 5분마다 한번 호출
        for nc in NewsCrawler.objects.all():
            chroma.get_or_create_collection(nc.collection_name)
            chroma.delete_collection(nc.collection_name)
