from functools import lru_cache
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
)


@lru_cache(maxsize=1)
def get_embedding(device="cuda"):
    if device:
        return SentenceTransformerEmbeddings(
            model_name="all-MiniLM-l6-v2", model_kwargs=dict(device=device)
        )

    return SentenceTransformerEmbeddings(model_name="all-MiniLM-l6-v2")