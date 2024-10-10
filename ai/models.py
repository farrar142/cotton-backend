from django.db import models
from users.models import User


# Create your models here.
class ChatBot(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="chatbots")
    character = models.TextField(default="")
