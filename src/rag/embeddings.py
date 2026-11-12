"""Embedding model configuration."""

from __future__ import annotations

import os
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings


DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return a cached multilingual embedding model.

    The model is initialized only once per process.
    """
    model_name = os.getenv(
        "EMBEDDING_MODEL",
        DEFAULT_EMBEDDING_MODEL,
    )

    device = os.getenv(
        "EMBEDDING_DEVICE",
        "cpu",
    )

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={
            "device": device,
        },
        encode_kwargs={
            "normalize_embeddings": True,
        },
    )