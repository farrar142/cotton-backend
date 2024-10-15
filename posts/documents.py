from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Post


@registry.register_document
class PostDocument(Document):
    user = fields.ObjectField(
        properties=dict(username=fields.TextField(), nickname=fields.TextField())
    )
    hashtags = fields.ListField(
        fields.ObjectField(properties=dict(text=fields.KeywordField()))
    )

    class Index:
        name = "posts"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Post  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            "text",
        ]

    def get_queryset(self):
        return (
            super().get_queryset().select_related("user").prefetch_related("hashtags")
        )
