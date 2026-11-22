"""Document loading and text extraction utilities."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
from uuid import uuid4

from langchain_core.documents import Document
from pypdf import PdfReader

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]


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
    if not raw_bytes:
        return None

    if Image is not None:
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

    # Fallback puro em Python caso Pillow não esteja disponível (suporta JPEG e PNG nativos)
    if raw_bytes.startswith(b"\xff\xd8\xff") or raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        if len(raw_bytes) > 1_500_000:
            return None
        return base64.b64encode(raw_bytes).decode("ascii"), 640, 480
    return None


def _ocr_imagem_bytes(raw_bytes: bytes) -> str:
    """Executa OCR leve via binário tesseract (se disponível) sobre bytes de imagem."""
    if not raw_bytes or not shutil.which("tesseract"):
        return ""
    try:
        img_input = raw_bytes
        if Image is not None:
            with Image.open(BytesIO(raw_bytes)) as img:
                rgb = img.convert("RGB")
                if max(rgb.width, rgb.height) > 1600:
                    rgb.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                buf = BytesIO()
                rgb.save(buf, format="PNG")
                img_input = buf.getvalue()

        for lang in ("por+eng", "por", "eng"):
            proc = subprocess.run(
                ["tesseract", "stdin", "stdout", "-l", lang, "--psm", "6"],
                input=img_input,
                capture_output=True,
                timeout=12,
                check=False,
            )
            if proc.returncode == 0:
                texto = proc.stdout.decode("utf-8", errors="ignore").strip()
                if texto:
                    return texto
    except Exception as e:
        print(f"[OCR] Aviso ao executar tesseract: {e}")
    return ""


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
                legenda_pagina = texto_pagina or _ocr_imagem_bytes(raw_data)
                diagramas.append(
                    {
                        "pagina": page_index + 1,
                        "nome": f"Diagrama / Figura {len(diagramas) + 1} (Pág. {page_index + 1})",
                        "largura": w,
                        "altura": h,
                        "base64": b64_str,
                        "data_url": f"data:image/jpeg;base64,{b64_str}",
                        "texto_pagina": legenda_pagina[:900],
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
    """Cria um Document indexável para imagens de diagramas enviadas diretamente (com OCR)."""
    convertido = _comprimir_imagem_para_base64(content)
    if not convertido:
        raise DocumentLoadingError(f"Imagem inválida ou muito pequena: {filename}")
    _, w, h = convertido
    extension = Path(filename).suffix.lower().lstrip(".")
    texto_ocr = _ocr_imagem_bytes(content)
    conteudo_doc = (
        f"Texto e rótulos extraídos do diagrama '{filename}':\n{texto_ocr}"
        if texto_ocr
        else (
            f"Diagrama técnico visual enviado no arquivo de imagem '{filename}' "
            f"(dimensões {w}x{h}px). Analise visualmente os componentes, conexões, "
            f"setas, rótulos e arquitetura representados na imagem do diagrama."
        )
    )
    return [
        Document(
            page_content=conteudo_doc,
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
    """Extract text from PDF pages (with automatic OCR fallback for slide/scanned PDFs)."""
    try:
        reader = PdfReader(BytesIO(content))
        documents = []
        total_pages = len(reader.pages)

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
                        "total_pages": total_pages,
                    },
                )
            )

        # Fallback Multimodal / OCR para PDFs de slides ou digitalizados (sem camada de texto)
        if not documents:
            for page_index, page in enumerate(reader.pages[:15]):
                try:
                    page_images = list(page.images)
                except Exception:
                    continue
                textos_ocr_pagina = []
                for img_file in page_images:
                    raw_data = getattr(img_file, "data", b"")
                    if not raw_data or len(raw_data) < 10000:
                        continue
                    ocr_txt = _ocr_imagem_bytes(raw_data)
                    if ocr_txt:
                        textos_ocr_pagina.append(ocr_txt)
                if textos_ocr_pagina:
                    documents.append(
                        Document(
                            page_content="\n\n".join(textos_ocr_pagina),
                            metadata={
                                "document_id": document_id,
                                "source": filename,
                                "file_type": "pdf",
                                "page": page_index + 1,
                                "total_pages": total_pages,
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