from typing import Callable, Iterable, TypeVar
import numpy as np
from django.core.cache import cache
from ..documents import PostDocument as PD
from ..models import models, Post


class RecommendService:
    def __init__(self):
        pass

    @classmethod
    def get_mean_vector(cls, ids: list[int]) -> list[float]:
        s = PD.search()
        r = s.query("ids", values=ids).execute()
        vectors = [hit.text_embedding for hit in r]
        return np.mean(vectors, axis=0)

    @classmethod
    def get_post_knn(cls, target_queries: Iterable[Post]):
        s = PD.search()
        ids = list(map(lambda x: x.pk, target_queries))
        mean_vector = cls.get_mean_vector(ids)
        r = s.exclude("ids", values=ids).knn(
            field="text_embedding", k=100, num_candidates=100, query_vector=mean_vector
        )
        return r.to_queryset()
