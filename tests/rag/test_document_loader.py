"""Tests for document loading."""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from src.rag.document_loader import (
    DocumentLoadingError,
    load_document,
)


def test_load_markdown():
    content = b"# Introduction\n\nRAG combines retrieval and generation."

    documents = load_document(
        content=content,
        filename="example.md",
        document_id="doc-123",
    )

    assert len(documents) == 1
    assert documents[0].metadata["document_id"] == "doc-123"
    assert documents[0].metadata["file_type"] == "md"
    assert "RAG" in documents[0].page_content


def test_load_text():
    documents = load_document(
        content=b"Simple text document.",
        filename="example.txt",
    )

    assert len(documents) == 1
    assert documents[0].page_content == "Simple text document."


def test_reject_empty_content():
    with pytest.raises(ValueError):
        load_document(
            content=b"",
            filename="example.txt",
        )


def test_reject_unsupported_extension():
    with pytest.raises(ValueError):
        load_document(
            content=b"invalid",
            filename="example.exe",
        )


def test_reject_invalid_pdf():
    with pytest.raises(DocumentLoadingError):
        load_document(
            content=b"not a real PDF",
            filename="invalid.pdf",
        )


def test_reject_pdf_without_extractable_text():
    buffer = BytesIO()

    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.write(buffer)

    with pytest.raises(DocumentLoadingError):
        load_document(
            content=buffer.getvalue(),
            filename="blank.pdf",
        )