from functools import lru_cache
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
)


import torch


@lru_cache(maxsize=1)
def get_embedding(device="cuda"):
    torch.multiprocessing.set_start_method("spawn")
    if device:
        return SentenceTransformerEmbeddings(
            model_name="all-MiniLM-l6-v2", model_kwargs=dict(device=device)
        )

    return SentenceTransformerEmbeddings(model_name="all-MiniLM-l6-v2")
