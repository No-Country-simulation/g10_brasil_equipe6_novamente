"""Tests for embedding generation."""

from src.rag.embeddings import get_embeddings


def test_embedding_dimension():
    embeddings = get_embeddings()

    vector = embeddings.embed_query(
        "What is retrieval augmented generation?"
    )

    assert len(vector) == 384


def test_embedding_cache():
    first = get_embeddings()
    second = get_embeddings()

    assert first is second


def test_embedding_similarity():
    embeddings = get_embeddings()

    vectors = embeddings.embed_documents(
        [
            "O que é inteligência artificial?",
            "Explique o conceito de inteligência artificial.",
            "Como preparar uma receita de bolo?",
        ]
    )

    assert len(vectors) == 3
    assert all(len(vector) == 384 for vector in vectors)