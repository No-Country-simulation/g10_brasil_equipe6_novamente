# Camada 1: Build (Compilação e Instalação)
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instala via requirements.txt de forma isolada (usando wheel CPU-only do PyTorch para reduzir ~2GB de imagem)
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt


# Camada 2: Runtime (Execução Final)
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local /usr/local

# Copia os arquivos como estao na arvore do repositorio
COPY api.py .
COPY requirements.txt .
COPY Contrato_interno.md .
COPY README.md .
COPY src/ ./src/
COPY infra/ ./infra/
COPY prompts_e_testes/ ./prompts_e_testes/
COPY documents/ ./documents/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]