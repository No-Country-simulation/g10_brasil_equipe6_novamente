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

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24 / 2.x
except ImportError:
    try:
        import fitz  # type: ignore[no-redef]
    except ImportError:
        fitz = None  # type: ignore[assignment]


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


def _comprimir_imagem_para_base64(
    raw_bytes: bytes,
    max_side: int = 960,
    min_width: int = 160,
    min_height: int = 120,
    max_aspect: float = 4.5,
) -> tuple[str, int, int, bool] | None:
    """Converte bytes de imagem para JPEG RGB (com fundo branco se houver transparência) em Base64.

    Retorna `(b64_str, largura, altura, tinha_transparencia)` ou `None` se rejeitada.
    """
    if not raw_bytes:
        return None

    if Image is not None:
        try:
            with Image.open(BytesIO(raw_bytes)) as img:
                width, height = img.size
                # Ignora ícones muito pequenos ou faixas/banners estreitos
                if width < min_width or height < min_height:
                    return None
                aspect = max(width / max(height, 1), height / max(width, 1))
                if aspect > max_aspect:
                    return None

                tinha_transparencia = img.mode in ("RGBA", "LA") or (
                    img.mode == "P" and "transparency" in img.info
                )
                if tinha_transparencia:
                    rgba = img.convert("RGBA")
                    fundo_branco = Image.new("RGB", rgba.size, (255, 255, 255))
                    fundo_branco.paste(rgba, mask=rgba.split()[3])
                    rgb_img = fundo_branco
                else:
                    rgb_img = img.convert("RGB")

                if max(width, height) > max_side:
                    rgb_img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

                out = BytesIO()
                rgb_img.save(out, format="JPEG", quality=82, optimize=True)
                b64_str = base64.b64encode(out.getvalue()).decode("ascii")
                return b64_str, rgb_img.width, rgb_img.height, tinha_transparencia
        except Exception:
            return None

    # Fallback puro em Python caso Pillow não esteja disponível (suporta JPEG e PNG nativos)
    if raw_bytes.startswith(b"\xff\xd8\xff") or raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        if len(raw_bytes) > 1_500_000:
            return None
        return base64.b64encode(raw_bytes).decode("ascii"), 640, 480, False
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


_PALAVRAS_PAGINA_ESTRUTURAL = (
    "safe harbor",
    "agenda",
    "table of contents",
    "sumário",
    "índice",
    "thank you",
    "obrigado",
    "obrigada",
    "questions?",
    "dúvidas?",
    "all rights reserved",
    "confidential",
)

_PALAVRAS_TECNICAS_DIAGRAMA = (
    "architecture",
    "arquitetura",
    "diagram",
    "diagrama",
    "figure",
    "figura",
    "fig.",
    "flow",
    "fluxo",
    "pipeline",
    "network",
    "subnet",
    "vcn",
    "vnic",
    "cluster",
    "node",
    "pod",
    "container",
    "kubernetes",
    "hypervisor",
    "scaling",
    "autoscaling",
    "instance",
    "storage",
    "database",
    "server",
    "gateway",
    "api",
    "layer",
    "camada",
    "sistema",
    "modelo",
    "componentes",
)


def _eh_pagina_estrutural(page_index: int, total_pages: int, texto_pagina: str) -> bool:
    """Identifica capas, contracapas, avisos legais, sumários e slides de encerramento."""
    texto_norm = " ".join(texto_pagina.lower().split())
    if total_pages >= 3:
        # Capa (página 1) com pouco texto técnico
        if page_index == 0 and len(texto_norm) < 280:
            return True
        # Última página (encerramento / Thank you / créditos)
        if page_index == total_pages - 1 and len(texto_norm) < 350:
            return True

    if any(termo in texto_norm for termo in _PALAVRAS_PAGINA_ESTRUTURAL) and len(texto_norm) < 650:
        return True

    # Slide de Summary / Resumo puramente em tópicos curtos
    if (texto_norm.startswith("summary") or texto_norm.startswith("resumo")) and len(texto_norm) < 220:
        return True

    return False


def _bonus_contexto_tecnico(texto_pagina: str) -> float:
    """Calcula pontuação semântica leve baseada em vocabulário técnico presente na página."""
    texto_norm = texto_pagina.lower()
    acertos = sum(1 for termo in _PALAVRAS_TECNICAS_DIAGRAMA if termo in texto_norm)
    return min(acertos * 6.0, 30.0)


def _coletar_candidatas_vetoriais_pymupdf(
    content: bytes,
    max_paginas_busca: int,
    max_renderizar: int = 4,
) -> list[dict]:
    """Detecta páginas ricas em diagramas vetoriais (ex.: slides/arquiteturas) via PyMuPDF."""
    if fitz is None:
        return []

    candidatas: list[dict] = []
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            total_pages = len(doc)
            limite = min(total_pages, max_paginas_busca)
            pontuacoes_paginas: list[tuple[float, int, str, int, int]] = []

            for page_index in range(limite):
                page = doc[page_index]
                texto_pagina = (page.get_text("text") or "").strip()
                if _eh_pagina_estrutural(page_index, total_pages, texto_pagina):
                    continue

                rect = page.rect
                area_pagina = max(rect.width * rect.height, 1.0)
                top_margin = rect.y0 + rect.height * 0.09
                bottom_margin = rect.y1 - rect.height * 0.08

                drawings = page.get_drawings() or []
                interior_rects = []
                n_drawings_relevantes = 0
                for d in drawings:
                    dr = d.get("rect")
                    if dr is None:
                        continue
                    # Ignora faixas de cabeçalho/rodapé e micro-artefatos
                    if dr.y1 <= top_margin or dr.y0 >= bottom_margin:
                        continue
                    if dr.width < 4 and dr.height < 4:
                        continue
                    # Ignora retângulo de fundo cobrindo a página inteira
                    if (dr.width * dr.height) / area_pagina > 0.88:
                        continue
                    n_drawings_relevantes += 1
                    interior_rects.append(dr)

                if n_drawings_relevantes < 16 or not interior_rects:
                    continue

                # Calcula área coberta pelos elementos vetoriais do miolo
                x0 = min(r.x0 for r in interior_rects)
                y0 = min(r.y0 for r in interior_rects)
                x1 = max(r.x1 for r in interior_rects)
                y1 = max(r.y1 for r in interior_rects)
                cobertura = max(0.0, (x1 - x0) * (y1 - y0)) / area_pagina
                if cobertura < 0.14:
                    continue

                # Conta rótulos curtos (típicos de caixas/setas de diagramas)
                blocos = page.get_text("blocks") or []
                rotulos_curtos = 0
                for b in blocos:
                    txt_b = (b[4] or "").strip() if len(b) > 4 else ""
                    if 2 <= len(txt_b) <= 45:
                        rotulos_curtos += 1

                # Conta imagens raster grandes já presentes na página (ex.: screenshots de tabelas)
                n_imgs = len(page.get_images(full=False) or [])

                score = (
                    42.0
                    + min(n_drawings_relevantes * 0.75, 38.0)
                    + min(cobertura * 45.0, 26.0)
                    + min(rotulos_curtos * 2.5, 22.0)
                    + _bonus_contexto_tecnico(texto_pagina)
                    + (8.0 if n_imgs >= 1 else 0.0)
                )
                pontuacoes_paginas.append(
                    (score, page_index, texto_pagina, n_drawings_relevantes, rotulos_curtos)
                )

            pontuacoes_paginas.sort(key=lambda item: item[0], reverse=True)

            for score, page_index, texto_pagina, _, _ in pontuacoes_paginas[:max_renderizar]:
                page = doc[page_index]
                # Renderiza com fundo branco (alpha=False) em resolução nítida e leve
                pix = page.get_pixmap(dpi=150, alpha=False)
                raw_png = pix.tobytes("png")
                convertido = _comprimir_imagem_para_base64(
                    raw_png, max_side=1024, min_width=200, min_height=140, max_aspect=4.5
                )
                if not convertido:
                    continue
                b64_str, w, h, _ = convertido
                candidatas.append(
                    {
                        "score": score,
                        "pagina": page_index + 1,
                        "origem": "vetorial",
                        "largura": w,
                        "altura": h,
                        "base64": b64_str,
                        "data_url": f"data:image/jpeg;base64,{b64_str}",
                        "texto_pagina": texto_pagina[:900],
                    }
                )
    except Exception as e:
        print(f"[Multimodal] Aviso ao analisar diagramas vetoriais via PyMuPDF: {e}")

    return candidatas


def extrair_diagramas_documento(
    content: bytes,
    filename: str,
    max_imagens: int = 2,
    max_paginas_busca: int = 25,
) -> list[dict]:
    """
    Extrai até `max_imagens` diagramas/figuras técnicas mais relevantes de um PDF ou imagem,
    combinando ranqueamento de imagens raster (descartando capas/logos repetidos) e
    renderização de páginas com diagramas vetoriais (via PyMuPDF), retornando Base64 JPEG.
    """
    extension = Path(filename).suffix.lower()

    if extension in IMAGE_EXTENSIONS:
        convertido = _comprimir_imagem_para_base64(content)
        if not convertido:
            return []
        b64_str, w, h, _ = convertido
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

    candidatas: list[dict] = []
    try:
        reader = PdfReader(BytesIO(content))
        total_pages = len(reader.pages)
        paginas_alvo = list(reader.pages[:max_paginas_busca])

        # Passo 1: identifica assinaturas repetidas entre páginas (logos, cabeçalhos, rodapés)
        ocorrencias_assinatura: dict[int, set[int]] = {}
        imagens_por_pagina: list[tuple[int, str, list[bytes]]] = []

        for page_index, page in enumerate(paginas_alvo):
            texto_pagina = (page.extract_text() or "").strip()
            try:
                imagens_pagina = list(page.images)
            except Exception:
                imagens_pagina = []

            raws_pagina: list[bytes] = []
            for img_file in imagens_pagina:
                raw_data = getattr(img_file, "data", b"")
                if not raw_data or len(raw_data) < 18000:
                    continue
                assinatura = hash(raw_data[:4096]) ^ len(raw_data)
                ocorrencias_assinatura.setdefault(assinatura, set()).add(page_index)
                raws_pagina.append(raw_data)

            imagens_por_pagina.append((page_index, texto_pagina, raws_pagina))

        # Passo 2: pontua candidatas raster únicas (sem parar na página 1)
        hashes_avaliados: set[int] = set()
        for page_index, texto_pagina, raws_pagina in imagens_por_pagina:
            eh_estrutural = _eh_pagina_estrutural(page_index, total_pages, texto_pagina)
            for raw_data in raws_pagina:
                assinatura = hash(raw_data[:4096]) ^ len(raw_data)
                if assinatura in hashes_avaliados:
                    continue
                # Descarta ativos repetidos em 2+ páginas (logos, templates, faixas)
                if total_pages >= 3 and len(ocorrencias_assinatura.get(assinatura, set())) >= 2:
                    continue

                convertido = _comprimir_imagem_para_base64(
                    raw_data, max_side=960, min_width=200, min_height=140, max_aspect=4.2
                )
                if not convertido:
                    continue

                hashes_avaliados.add(assinatura)
                b64_str, w, h, tinha_transparencia = convertido
                area = w * h
                aspect = max(w / max(h, 1), h / max(w, 1))

                score = 35.0
                score += min(area / 22000.0, 28.0)
                if 1.05 <= aspect <= 2.4:
                    score += 10.0
                score += _bonus_contexto_tecnico(texto_pagina)
                if len(texto_pagina) >= 120:
                    score += 10.0

                # Penaliza fortemente capas, contracapas e arte decorativa transparente
                if eh_estrutural:
                    score -= 110.0
                if tinha_transparencia:
                    score -= 35.0 if page_index in (0, total_pages - 1) else 12.0

                # Se tesseract estiver instalado, premia imagens que contêm texto/rótulos técnicos
                ocr_txt = ""
                if not eh_estrutural and score >= 35.0:
                    ocr_txt = _ocr_imagem_bytes(raw_data)
                    n_palavras_ocr = len(ocr_txt.split())
                    if n_palavras_ocr >= 4:
                        score += min(n_palavras_ocr * 2.0, 30.0)
                    elif tinha_transparencia and n_palavras_ocr == 0:
                        score -= 25.0

                legenda_pagina = texto_pagina or ocr_txt
                candidatas.append(
                    {
                        "score": score,
                        "pagina": page_index + 1,
                        "origem": "raster",
                        "largura": w,
                        "altura": h,
                        "base64": b64_str,
                        "data_url": f"data:image/jpeg;base64,{b64_str}",
                        "texto_pagina": legenda_pagina[:900],
                    }
                )
    except Exception as e:
        print(f"[Multimodal] Aviso ao extrair diagramas raster do PDF: {e}")

    # Passo 3: complementa com páginas ricas em diagramas vetoriais (PyMuPDF)
    candidatas.extend(
        _coletar_candidatas_vetoriais_pymupdf(
            content,
            max_paginas_busca=max_paginas_busca,
            max_renderizar=max(max_imagens + 2, 4),
        )
    )

    if not candidatas:
        return []

    # Passo 4: seleciona as top `max_imagens`, priorizando páginas distintas e descartando capas quando há algo melhor
    candidatas.sort(key=lambda item: item["score"], reverse=True)
    positivas = [c for c in candidatas if c["score"] > 0]
    pool = positivas if positivas else candidatas

    selecionadas: list[dict] = []
    paginas_usadas: set[int] = set()
    for cand in pool:
        if len(selecionadas) >= max_imagens:
            break
        if cand["pagina"] in paginas_usadas:
            continue
        paginas_usadas.add(cand["pagina"])
        selecionadas.append(cand)

    # Fallback: se só havia 1 página com várias imagens úteis, completa até max_imagens
    if len(selecionadas) < max_imagens:
        for cand in pool:
            if len(selecionadas) >= max_imagens:
                break
            if cand not in selecionadas:
                selecionadas.append(cand)

    # Ordena por página crescente para leitura natural na interface
    selecionadas.sort(key=lambda item: item["pagina"])

    diagramas: list[dict] = []
    for idx, item in enumerate(selecionadas, start=1):
        rotulo_tipo = (
            "Diagrama Técnico" if item["origem"] == "vetorial" else "Diagrama / Figura"
        )
        diagramas.append(
            {
                "pagina": item["pagina"],
                "nome": f"{rotulo_tipo} {idx} (Pág. {item['pagina']})",
                "largura": item["largura"],
                "altura": item["altura"],
                "base64": item["base64"],
                "data_url": item["data_url"],
                "texto_pagina": item["texto_pagina"],
            }
        )

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
    _, w, h, _ = convertido
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