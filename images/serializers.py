from rest_framework import serializers
from commons.serializers import Base64Serializer

from .models import Image
from .tasks import resize_image_model


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image

        fields = ("id", "url", "small", "medium", "large")

    url = Base64Serializer()
    small = Base64Serializer(required=False)
    medium = Base64Serializer(required=False)
    large = Base64Serializer(required=False)

    def create(self, validated_data):
        instance = super().create(validated_data)
        print(f"{instance.pk=}")
        resize_image_model.delay(instance.pk)
        return instance
