"""Tests for ChromaDB vector store operations."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings

from src.rag.vector_store import (
    delete_document,
    index_documents,
)


def test_index_and_delete_documents(tmp_path):
    vector_store = Chroma(
        collection_name="test_documents",
        embedding_function=FakeEmbeddings(size=384),
        persist_directory=str(tmp_path / "chroma"),
    )

    documents = [
        Document(
            page_content="RAG retrieves relevant information.",
            metadata={
                "document_id": "doc-123",
                "chunk_index": 0,
            },
        ),
        Document(
            page_content="Embeddings represent semantic meaning.",
            metadata={
                "document_id": "doc-123",
                "chunk_index": 1,
            },
        ),
    ]

    indexed_count = index_documents(
        documents,
        vector_store=vector_store,
    )

    assert indexed_count == 2

    stored = vector_store.get(
        where={"document_id": "doc-123"}
    )

    assert len(stored["ids"]) == 2

    deleted_count = delete_document(
        document_id="doc-123",
        vector_store=vector_store,
    )

    assert deleted_count == 2

    remaining = vector_store.get(
        where={"document_id": "doc-123"}
    )

    assert len(remaining["ids"]) == 0


def test_reindex_does_not_duplicate_chunks(tmp_path):
    vector_store = Chroma(
        collection_name="test_reindex",
        embedding_function=FakeEmbeddings(size=384),
        persist_directory=str(tmp_path / "chroma"),
    )

    documents = [
        Document(
            page_content="Example content.",
            metadata={
                "document_id": "doc-123",
                "chunk_index": 0,
            },
        )
    ]

    index_documents(documents, vector_store)
    index_documents(documents, vector_store)

    stored = vector_store.get(
        where={"document_id": "doc-123"}
    )

    assert len(stored["ids"]) == 1