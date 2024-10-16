from typing import Any
import elasticsearch_dsl as dsl
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import Post, Favorite, Hashtag, Repost, User


class DenseVector(fields.DEDField, fields.Field):
    name = "dense_vector"
    dims = 384

    def __init__(self, attr=None, **kwargs):
        super(DenseVector, self).__init__(attr=attr, dims=self.dims, **kwargs)


@registry.register_document
class PostDocument(Document):
    user = fields.ObjectField(
        properties=dict(
            username=fields.TextField(),
            nickname=fields.TextField(),
            is_protected=fields.BooleanField(),
        )
    )
    hashtags = fields.ListField(
        fields.ObjectField(properties=dict(text=fields.KeywordField()))
    )
    favorites = fields.ListField(
        fields.ObjectField(
            properties=dict(
                user=fields.IntegerField("user_id"),
                post=fields.IntegerField("post_id"),
            )
        )
    )
    reposts = fields.ListField(
        fields.ObjectField(
            properties=dict(
                user=fields.IntegerField("user_id"),
                post=fields.IntegerField("post_id"),
            )
        )
    )

    text_embedding = DenseVector()
    text = fields.TextField("text", fielddata=True, analyzer="nori")

    def prepare_text_embedding(self, instance: Post):
        from ai.embeddings import embedding

        return embedding.embed_query(instance.text)

    class Index:
        name = "posts"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Post  # The model associated with this Document
        queryset_pagination = 1000
        # The fields of the model you want to be indexed in Elasticsearch
        fields = ["created_at"]
        related_models = [Favorite, Repost]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("user")
            .prefetch_related("hashtags", "favorites", "reposts")
        )

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, (Favorite, Hashtag, Repost)):
            return related_instance.post
        elif isinstance(related_instance, User):
            return related_instance.post_set.all()
