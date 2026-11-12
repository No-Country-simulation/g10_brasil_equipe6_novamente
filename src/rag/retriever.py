"""Semantic document retrieval."""

from __future__ import annotations

from typing import Literal

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.rag.vector_store import get_vector_store


SearchType = Literal["similarity", "mmr"]


def retrieve_documents(
    query: str,
    document_id: str,
    *,
    vector_store: Chroma | None = None,
    search_type: SearchType = "mmr",
    k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.7,
) -> list[Document]:
    """
    Retrieve relevant chunks from a specific document.

    All searches are filtered by document_id.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not document_id.strip():
        raise ValueError("document_id cannot be empty.")

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    if fetch_k < k:
        raise ValueError(
            "fetch_k must be greater than or equal to k."
        )

    if not 0.0 <= lambda_mult <= 1.0:
        raise ValueError(
            "lambda_mult must be between 0 and 1."
        )

    if search_type not in ("similarity", "mmr"):
        raise ValueError(
            f"Unsupported search type: {search_type}"
        )

    vector_store = (
        vector_store
        if vector_store is not None
        else get_vector_store()
    )

    document_filter = {
        "document_id": document_id,
    }

    if search_type == "similarity":
        return vector_store.similarity_search(
            query=query,
            k=k,
            filter=document_filter,
        )

    return vector_store.max_marginal_relevance_search(
        query=query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
        filter=document_filter,
    )