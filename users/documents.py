import numpy as np
from typing import Any
import elasticsearch_dsl as dsl
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import User


class DenseVector(fields.DEDField, fields.Field):
    name = "dense_vector"

    def __init__(self, attr=None, **kwargs):
        dims = 384
        super(DenseVector, self).__init__(attr=attr, dims=dims, **kwargs)


@registry.register_document
class UserDocument(Document):
    post_embedding = DenseVector()

    def prepare_post_embedding(self, instance: User):
        from ai.embeddings import embedding

        posts = instance.post_set.all()
        if len(posts):
            embeddings = [embedding.embed_query(p.text) for p in posts]
            return np.mean(embeddings, axis=0)
        return embedding.embed_query("")

    class Index:
        name = "users"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = User  # The model associated with this Document
        queryset_pagination = 1000
        # The fields of the model you want to be indexed in Elasticsearch
        fields = ["username", "nickname", "bio", "is_protected"]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("post_set")
