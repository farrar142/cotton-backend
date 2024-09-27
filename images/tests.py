import base64
from base.test import TestCase


# Create your tests here.
class TestImage(TestCase):
    def test_image(self):
        with open("./commons/cat.jpg", "rb") as clipped_file:
            clipped_image = clipped_file.read()
        b64_str = base64.b64encode(clipped_image)
        from .serializers import ImageSerializer

        serializer = ImageSerializer(data=dict(url=b64_str.decode("utf-8")))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer.instance.refresh_from_db()
        print(serializer.data)
