"""Benchmark different document chunking configurations."""

from __future__ import annotations

from pathlib import Path
from statistics import mean, median

from src.rag.document_loader import load_document
from src.rag.text_splitter import (
    ChunkingConfig,
    split_documents,
)


CONFIGURATIONS = [
    ChunkingConfig(chunk_size=500, chunk_overlap=100),
    ChunkingConfig(chunk_size=1000, chunk_overlap=200),
    ChunkingConfig(chunk_size=1500, chunk_overlap=300),
    ChunkingConfig(chunk_size=2000, chunk_overlap=400),
]


def benchmark_chunking(file_path: Path) -> None:
    """Compare chunk sizes for a given document."""

    documents = load_document(
        content=file_path.read_bytes(),
        filename=file_path.name,
    )

    print(f"\nDocument: {file_path.name}")
    print(f"Pages/Documents: {len(documents)}")

    print("\n=== CHUNKING BENCHMARK ===")

    for config in CONFIGURATIONS:
        chunks = split_documents(
            documents=documents,
            config=config,
        )

        sizes = [
            len(chunk.page_content)
            for chunk in chunks
        ]

        if not sizes:
            continue

        print(
            f"\nChunk size: {config.chunk_size}"
            f"\nOverlap: {config.chunk_overlap}"
            f"\nTotal chunks: {len(chunks)}"
            f"\nAverage length: {mean(sizes):.2f}"
            f"\nMedian length: {median(sizes):.2f}"
            f"\nMinimum length: {min(sizes)}"
            f"\nMaximum length: {max(sizes)}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark RAG chunking configurations."
    )

    parser.add_argument(
        "file",
        type=Path,
        help="Path to a PDF, Markdown or TXT document.",
    )

    args = parser.parse_args()

    benchmark_chunking(args.file)