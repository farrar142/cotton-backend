from typing import Iterable
import numpy as np
from ..documents import PostDocument as PD
from ..models import models, Post


class PostSelector:
    def __init__(self):
        pass

    def get_post_knn(self, target_queries: Iterable[Post]):
        s = PD.search()
        ids = list(map(lambda x: x.pk, target_queries))
        r = s.query("ids", values=ids).execute()
        vectors = [hit.text_embedding for hit in r]
        mean_vector = np.mean(vectors, axis=0)

        r = s.knn(
            field="text_embedding", k=10, num_candidates=10, query_vector=mean_vector
        ).exclude("ids", values=ids)
        return r.to_queryset()
