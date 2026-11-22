"""Document loading and text extraction utilities."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document
from PIL import Image
from pypdf import PdfReader


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"} | IMAGE_EXTENSIONS


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

    if extension in IMAGE_EXTENSIONS:
        return _load_image_document(content, filename, document_id)

    return _load_text(content, filename, document_id)


def _comprimir_imagem_para_base64(raw_bytes: bytes, max_side: int = 768) -> tuple[str, int, int] | None:
    """Converte bytes de imagem para JPEG RGB redimensionado em Base64."""
    try:
        with Image.open(BytesIO(raw_bytes)) as img:
            width, height = img.size
            # Ignora ícones muito pequenos ou faixas/banners estreitos
            if width < 160 or height < 120:
                return None
            aspect = max(width / max(height, 1), height / max(width, 1))
            if aspect > 5.5:
                return None

            rgb_img = img.convert("RGB")
            if max(width, height) > max_side:
                rgb_img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

            out = BytesIO()
            rgb_img.save(out, format="JPEG", quality=75, optimize=True)
            b64_str = base64.b64encode(out.getvalue()).decode("ascii")
            return b64_str, rgb_img.width, rgb_img.height
    except Exception:
        return None


def extrair_diagramas_documento(
    content: bytes,
    filename: str,
    max_imagens: int = 2,
    max_paginas_busca: int = 15,
) -> list[dict]:
    """
    Extrai até `max_imagens` diagramas/figuras relevantes de um PDF ou arquivo de imagem,
    retornando Base64 JPEG leve + texto/legenda da página correspondente.
    """
    extension = Path(filename).suffix.lower()

    if extension in IMAGE_EXTENSIONS:
        convertido = _comprimir_imagem_para_base64(content)
        if not convertido:
            return []
        b64_str, w, h = convertido
        return [
            {
                "pagina": 1,
                "nome": f"Diagrama Técnico ({filename})",
                "largura": w,
                "altura": h,
                "base64": b64_str,
                "data_url": f"data:image/jpeg;base64,{b64_str}",
                "texto_pagina": f"Imagem de diagrama técnico enviada diretamente: {filename}",
            }
        ]

    if extension != ".pdf":
        return []

    diagramas: list[dict] = []
    hashes_vistos: set[int] = set()
    try:
        reader = PdfReader(BytesIO(content))
        for page_index, page in enumerate(reader.pages[:max_paginas_busca]):
            if len(diagramas) >= max_imagens:
                break
            try:
                imagens_pagina = list(page.images)
            except Exception:
                continue

            texto_pagina = (page.extract_text() or "").strip()
            for img_idx, img_file in enumerate(imagens_pagina):
                if len(diagramas) >= max_imagens:
                    break
                raw_data = getattr(img_file, "data", b"")
                # Filtra logos/ícones pequenos (< 18 KB)
                if not raw_data or len(raw_data) < 18000:
                    continue
                assinatura = hash(raw_data[:4096]) ^ len(raw_data)
                if assinatura in hashes_vistos:
                    continue

                convertido = _comprimir_imagem_para_base64(raw_data)
                if not convertido:
                    continue

                hashes_vistos.add(assinatura)
                b64_str, w, h = convertido
                diagramas.append(
                    {
                        "pagina": page_index + 1,
                        "nome": f"Diagrama / Figura {len(diagramas) + 1} (Pág. {page_index + 1})",
                        "largura": w,
                        "altura": h,
                        "base64": b64_str,
                        "data_url": f"data:image/jpeg;base64,{b64_str}",
                        "texto_pagina": texto_pagina[:900],
                    }
                )
    except Exception as e:
        print(f"[Multimodal] Aviso ao extrair diagramas do PDF: {e}")

    return diagramas


def _load_image_document(
    content: bytes,
    filename: str,
    document_id: str,
) -> list[Document]:
    """Cria um Document indexável para imagens de diagramas enviadas diretamente."""
    convertido = _comprimir_imagem_para_base64(content)
    if not convertido:
        raise DocumentLoadingError(f"Imagem inválida ou muito pequena: {filename}")
    _, w, h = convertido
    extension = Path(filename).suffix.lower().lstrip(".")
    return [
        Document(
            page_content=(
                f"Diagrama técnico visual enviado no arquivo de imagem '{filename}' "
                f"(dimensões {w}x{h}px). Analise visualmente os componentes, conexões, "
                f"setas, rótulos e arquitetura representados na imagem do diagrama."
            ),
            metadata={
                "document_id": document_id,
                "source": filename,
                "file_type": extension,
                "page": 1,
                "total_pages": 1,
            },
        )
    ]


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