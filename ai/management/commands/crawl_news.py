import os
import threading

from django.utils import autoreload

from django.core.management.base import BaseCommand, CommandError
from ...tasks import crawl_news


class Command(BaseCommand):
    help = "Crawl news"

    def handle(self, tests=[], *args, **options):
        crawl_news.delay()
