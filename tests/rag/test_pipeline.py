"""Integration tests for the RAG pipeline."""

from langchain_chroma import Chroma
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.rag.pipeline import RAGPipeline
from src.rag.text_splitter import ChunkingConfig


def test_ingest_and_search(tmp_path):
    vector_store = Chroma(
        collection_name="test_pipeline",
        embedding_function=DeterministicFakeEmbedding(size=384),
        persist_directory=str(tmp_path / "chroma"),
    )

    pipeline = RAGPipeline(
        vector_store=vector_store,
        chunking_config=ChunkingConfig(
            chunk_size=200,
            chunk_overlap=40,
        ),
    )

    content = (
        "Retrieval augmented generation combines "
        "document retrieval with language models. "
    ) * 20

    result = pipeline.ingest(
        content=content.encode("utf-8"),
        filename="rag.txt",
        document_id="doc-123",
    )

    assert result.document_id == "doc-123"
    assert result.chunk_count > 0

    documents = pipeline.search(
        query="What is retrieval augmented generation?",
        document_id="doc-123",
        search_type="similarity",
        k=3,
    )

    assert len(documents) > 0

    for document in documents:
        assert document.metadata["document_id"] == "doc-123"


def test_document_isolation(tmp_path):
    vector_store = Chroma(
        collection_name="test_isolation",
        embedding_function=DeterministicFakeEmbedding(size=384),
        persist_directory=str(tmp_path / "chroma"),
    )

    pipeline = RAGPipeline(vector_store=vector_store)

    pipeline.ingest(
        content=b"Document about artificial intelligence.",
        filename="ai.txt",
        document_id="doc-ai",
    )

    pipeline.ingest(
        content=b"Document about computer networks.",
        filename="networks.txt",
        document_id="doc-networks",
    )

    results = pipeline.search(
        query="What is artificial intelligence?",
        document_id="doc-ai",
        search_type="similarity",
        k=5,
    )

    assert results

    assert all(
        document.metadata["document_id"] == "doc-ai"
        for document in results
    )