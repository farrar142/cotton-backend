from typing import Self
import urllib.parse
from django.db import models
from users.models import User


# Create your models here.


class NewsCrawler(models.Model):
    collection_name = models.TextField(default="huffington")
    news_url = models.URLField(default="https://huffpost.com")
    url_icontains = models.CharField(max_length=255, default="/entry/")
    article_tag = models.CharField(max_length=63, default="main")
    article_id = models.CharField(max_length=63, default="main")


class ChatBot(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="chatbots")
    character = models.TextField(default="")
    news_subscriptions: "models.ManyToManyField[NewsCrawler,Self]" = (
        models.ManyToManyField(NewsCrawler, related_name="chatbots")
    )
