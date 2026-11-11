"""Tests for document chunking."""

import pytest

from langchain_core.documents import Document

from src.rag.text_splitter import (
    ChunkingConfig,
    is_meaningful_chunk,
    split_documents,
)


def test_split_documents():
    documents = [
        Document(
            page_content="RAG combines retrieval and generation. " * 100,
            metadata={
                "document_id": "doc-123",
                "source": "example.txt",
            },
        )
    ]

    chunks = split_documents(
        documents,
        ChunkingConfig(
            chunk_size=200,
            chunk_overlap=40,
        ),
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert len(chunk.page_content) <= 200
        assert chunk.metadata["document_id"] == "doc-123"
        assert "chunk_index" in chunk.metadata
        assert "start_index" in chunk.metadata


def test_empty_documents():
    assert split_documents([]) == []


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=0)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        ChunkingConfig(
            chunk_size=100,
            chunk_overlap=100,
        )


def test_negative_overlap():
    with pytest.raises(ValueError):
        ChunkingConfig(
            chunk_size=100,
            chunk_overlap=-1,
        )

def test_reject_short_numeric_chunk():
    document = Document(page_content="42")

    assert not is_meaningful_chunk(document)


def test_preserve_meaningful_short_chunk():
    document = Document(page_content="Introduction")

    assert is_meaningful_chunk(document)