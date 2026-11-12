"""Document loading and text extraction utilities."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"}


class DocumentLoadingError(Exception):
    """Raised when a document cannot be loaded or parsed."""


def load_document(
    content: bytes,
    filename: str,
    document_id: str | None = None,
) -> list[Document]:
    """
    Extract text from a supported document.

    Args:
        content: Raw document bytes.
        filename: Original filename.
        document_id: Optional unique document identifier.

    Returns:
        A list of LangChain Document objects.

    Raises:
        ValueError: If the file type or content is invalid.
        DocumentLoadingError: If document parsing fails.
    """
    if not content:
        raise ValueError("Document content cannot be empty.")

    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty.")

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension: {extension}"
        )

    document_id = document_id or str(uuid4())

    if extension == ".pdf":
        return _load_pdf(content, filename, document_id)

    return _load_text(content, filename, document_id)


def _load_pdf(
    content: bytes,
    filename: str,
    document_id: str,
) -> list[Document]:
    """Extract text from PDF pages."""
    try:
        reader = PdfReader(BytesIO(content))
        documents = []

        for page_index, page in enumerate(reader.pages):
            text = page.extract_text() or ""

            if not text.strip():
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "document_id": document_id,
                        "source": filename,
                        "file_type": "pdf",
                        "page": page_index + 1,
                        "total_pages": len(reader.pages),
                    },
                )
            )

        if not documents:
            raise DocumentLoadingError(
                "PDF does not contain extractable text."
            )

        return documents

    except DocumentLoadingError:
        raise
    except Exception as exc:
        raise DocumentLoadingError(
            f"Failed to parse PDF: {filename}"
        ) from exc


def _load_text(
    content: bytes,
    filename: str,
    document_id: str,
) -> list[Document]:
    """Decode Markdown or plain text documents."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentLoadingError(
            "Text document must use UTF-8 encoding."
        ) from exc

    if not text.strip():
        raise DocumentLoadingError(
            "Document does not contain readable text."
        )

    extension = Path(filename).suffix.lower()

    return [
        Document(
            page_content=text,
            metadata={
                "document_id": document_id,
                "source": filename,
                "file_type": extension.lstrip("."),
            },
        )
    ]