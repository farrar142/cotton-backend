import os
import uuid
from typing import TypeVar

from django.db import models
from django.utils.deconstruct import deconstructible
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# Create your models here.

T = TypeVar("T", bound=models.Model)


# def image_upload_to(prefix: str):
#     def wrapper(instance: T, filename):
#         ctype = ContentType.objects.get_for_model(instance.__class__)
#         ext = os.path.splitext(filename)[-1]
#         return f"{ctype.name}:{instance.pk}/{prefix}/{uuid.uuid4()}.{ext}"

#     return wrapper


@deconstructible
class image_upload_to:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, instance: T, filename: str):
        ctype = ContentType.objects.get_for_model(instance.__class__)
        ext = os.path.splitext(filename)[-1]
        return f"{ctype.name}:{instance.pk}/{self.prefix}/{uuid.uuid4()}.{ext.replace('.','')}"


original = image_upload_to("original")
small = image_upload_to("small")
medium = image_upload_to("medium")


class Image(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.ImageField(upload_to=original, null=True)
    small = models.ImageField(upload_to=small, null=True)  # 50
    medium = models.ImageField(upload_to=medium, null=True)  # 200
    large = models.ImageField(upload_to=image_upload_to("large"), null=True)  # 600

    def save(self, *args, **kwargs) -> None:
        url = None
        if self.pk == None:
            url = self.url
            self.url = None
        super().save(*args, **kwargs)
        if url:
            self.url = url
            self.save()
