"""ChromaDB vector store management."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.rag.embeddings import get_embeddings


DEFAULT_COLLECTION_NAME = "novamente_documents"
DEFAULT_PERSIST_DIRECTORY = ".data/chroma"


def get_vector_store() -> Chroma:
    """Create or load the persistent ChromaDB collection."""
    persist_directory = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        DEFAULT_PERSIST_DIRECTORY,
    )

    collection_name = os.getenv(
        "CHROMA_COLLECTION_NAME",
        DEFAULT_COLLECTION_NAME,
    )

    Path(persist_directory).mkdir(
        parents=True,
        exist_ok=True,
    )

    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=persist_directory,
    )


def generate_chunk_id(
    document: Document,
) -> str:
    """
    Generate a deterministic chunk identifier.

    The identifier depends on the document ID,
    chunk position and chunk content.
    """
    document_id = document.metadata.get("document_id")

    if not document_id:
        raise ValueError(
            "Chunk metadata must contain document_id."
        )

    chunk_index = document.metadata.get("chunk_index")

    if chunk_index is None:
        raise ValueError(
            "Chunk metadata must contain chunk_index."
        )

    raw_value = (
        f"{document_id}:"
        f"{chunk_index}:"
        f"{document.page_content}"
    )

    return hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()


def index_documents(
    documents: list[Document],
    vector_store: Chroma | None = None,
) -> int:
    """
    Replace all indexed chunks for one document.

    Returns the number of indexed chunks.
    """
    if not documents:
        return 0

    vector_store = (
        vector_store
        if vector_store is not None
        else get_vector_store()
    )

    document_ids = {
        document.metadata.get("document_id")
        for document in documents
    }

    if None in document_ids or len(document_ids) != 1:
        raise ValueError(
            "All chunks must have the same document_id."
        )

    document_id = next(iter(document_ids))

    chunk_ids = [
        generate_chunk_id(document)
        for document in documents
    ]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError(
            "Duplicate chunk identifiers detected."
        )

    delete_document(
        document_id=document_id,
        vector_store=vector_store,
    )

    vector_store.add_documents(
        documents=documents,
        ids=chunk_ids,
    )

    return len(documents)


def delete_document(
    document_id: str,
    vector_store: Chroma | None = None,
) -> int:
    """
    Delete all indexed chunks belonging to a document.

    Returns the number of deleted chunks.
    """
    vector_store = (
        vector_store
        if vector_store is not None
        else get_vector_store()
    )

    existing = vector_store.get(
        where={"document_id": document_id},
    )

    ids = existing.get("ids", [])

    if not ids:
        return 0

    vector_store.delete(ids=ids)

    return len(ids)