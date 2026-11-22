"""RAG ingestion and retrieval pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import os
from uuid import uuid4

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.rag.document_loader import load_document
from src.rag.retriever import SearchType, retrieve_documents
from src.rag.text_splitter import (
    ChunkingConfig,
    split_documents,
)
from src.rag.vector_store import (
    delete_document,
    get_vector_store,
    index_documents,
)


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Result of a document ingestion operation."""

    document_id: str
    filename: str
    page_count: int
    chunk_count: int


class RAGPipeline:
    """Coordinate document ingestion and semantic retrieval."""

    def __init__(
        self,
        vector_store: Chroma | None = None,
        chunking_config: ChunkingConfig | None = None,
    ) -> None:
        self.vector_store = (
            vector_store
            if vector_store is not None
            else get_vector_store()
        )

        self.chunking_config = (
            chunking_config or ChunkingConfig()
        )

    def ingest(
        self,
        content: bytes,
        filename: str,
        document_id: str | None = None,
    ) -> IngestionResult:
        """
        Load, split, embed and index a document.
        """
        document_id = document_id or str(uuid4())

        documents = load_document(
            content=content,
            filename=filename,
            document_id=document_id,
        )

        chunks = split_documents(
            documents=documents,
            config=self.chunking_config,
        )

        if not chunks:
            raise ValueError(
                "No valid chunks were generated."
            )

        max_chunks = int(os.getenv("RAG_MAX_CHUNKS", "0"))
        if max_chunks > 0 and len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]

        chunk_count = index_documents(
            documents=chunks,
            vector_store=self.vector_store,
        )

        return IngestionResult(
            document_id=document_id,
            filename=filename,
            page_count=len(documents),
            chunk_count=chunk_count,
        )

    def search(
        self,
        query: str,
        document_id: str,
        *,
        search_type: SearchType = "mmr",
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.7,
    ) -> list[Document]:
        """Retrieve relevant chunks from a document."""
        return retrieve_documents(
            query=query,
            document_id=document_id,
            vector_store=self.vector_store,
            search_type=search_type,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
        )

    def delete(self, document_id: str) -> int:
        """Remove a document from the vector store."""
        return delete_document(
            document_id=document_id,
            vector_store=self.vector_store,
        )