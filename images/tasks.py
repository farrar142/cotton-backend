from io import BytesIO
import PIL.Image as IMG
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import ImageFieldFile
from commons.celery import shared_task
from .models import Image


def resize_image(file: ImageFieldFile, MAX_SIZE: int):
    with IMG.open(fp=file) as img:
        width, height = img.size
        max_size = max([width, height])
        ratio = MAX_SIZE / max_size
        new_size: tuple[int, int] = tuple(
            map(lambda x: int(x * ratio), (width, height))  # type:ignore
        )
        img = img.resize(new_size)
        io = BytesIO()
        img.save(io, format="png")
        simple_file = InMemoryUploadedFile(
            file=io,
            field_name=None,
            name="image.png",
            content_type="image/png",
            size=io.tell(),
            charset=None,
        )
        return simple_file


@shared_task()
def resize_image_model(image_id):
    image = Image.objects.filter(id=image_id).first()
    if not image:
        return
    if not image.url:
        return
    file = image.url.open("rb")
    image.small = resize_image(file, 50)  # type:ignore
    image.medium = resize_image(file, 200)  # type:ignore
    image.large = resize_image(file, 600)  # type:ignore
    image.save()
