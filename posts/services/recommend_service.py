from typing import Callable, Iterable, TypeVar, TypedDict
import numpy as np
from elasticsearch_dsl import Q, A
from django.utils.timezone import localtime, timedelta
from users.documents import UserDocument as UD
from ..documents import DenseVector, PostDocument as PD
from ..models import models, Post, User


class Keyword(TypedDict):
    key: str
    doc_count: int


class RecommendService:
    @classmethod
    def get_users_related_posts(cls, user: User):
        favorite_post = models.Q(favorites__user=user)
        repost_post = models.Q(reposts__user=user)
        return Post.objects.filter(favorite_post | repost_post).order_by("-created_at")[
            :10
        ]

    @classmethod
    def get_mean_vector(cls, ids: list[int]) -> list[float]:
        s = PD.search()
        r = s.query("ids", values=ids).execute()
        if vectors := [hit.text_embedding for hit in r]:
            return np.mean(vectors, axis=0)
        return [0.0 for _ in range(DenseVector.dims)]

    @classmethod
    def get_post_knn(cls, target_queries: Iterable[Post]):
        s = PD.search()
        ids = list(map(lambda x: x.pk, target_queries))
        mean_vector = cls.get_mean_vector(ids)
        r = s.exclude("ids", values=ids).knn(
            field="text_embedding", k=100, num_candidates=100, query_vector=mean_vector
        )[:100]
        return r.to_queryset()

    @classmethod
    def get_user_knn(cls, target_queries: Iterable[Post]):
        ids = list(map(lambda x: x.pk, target_queries))
        mean_vector = cls.get_mean_vector(ids)

        us = UD.search()
        r = us.knn(
            field="post_embedding",
            k=100,
            num_candidates=100,
            query_vector=mean_vector,
            filter=Q("term", is_protected=False),
        )[:100]
        return r.to_queryset()

    @classmethod
    def get_top_terms_hashtag(cls) -> list[Keyword]:
        now = localtime() - timedelta(days=1)
        s = PD.search()
        agg = A("terms", field="hashtags.text", size=10)
        s = s.filter("range", created_at={"gte": now}).filter(
            "term", user__is_protected=False
        )
        s.aggs.bucket("top_terms", agg)
        r = s.execute()
        return [*r.aggregations.top_terms.buckets]
