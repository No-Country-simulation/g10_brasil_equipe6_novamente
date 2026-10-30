"""Document chunking and text filtering utilities."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    """Configuration for document chunking."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    def __post_init__(self) -> None:
        """Validate chunking configuration."""

        if self.chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if self.chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )


def is_meaningful_chunk(document: Document) -> bool:
    """
    Check whether a chunk contains meaningful text.

    Filters:
        - Empty or whitespace-only chunks.
        - Short numeric-only chunks, such as isolated page numbers.

    Args:
        document: LangChain Document to validate.

    Returns:
        True if the chunk should be retained.
    """
    content = document.page_content.strip()

    if not content:
        return False

    if content.isdigit() and len(content) <= 3:
        return False

    return True


def split_documents(
    documents: list[Document],
    config: ChunkingConfig | None = None,
) -> list[Document]:
    """
    Split documents into smaller, meaningful chunks.

    The function:
        1. Validates the chunking configuration.
        2. Splits documents using RecursiveCharacterTextSplitter.
        3. Removes empty and short numeric-only chunks.
        4. Preserves original document metadata.
        5. Adds sequential chunk indices.

    Args:
        documents: List of LangChain Document objects.
        config: Optional chunking configuration.

    Returns:
        A list of filtered Document chunks.
    """
    config = config or ChunkingConfig()

    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        add_start_index=True,
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    valid_chunks = [
        chunk
        for chunk in chunks
        if is_meaningful_chunk(chunk)
    ]

    for index, chunk in enumerate(valid_chunks):
        chunk.metadata["chunk_index"] = index

    return valid_chunks