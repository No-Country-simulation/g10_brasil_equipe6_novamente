# Camada 1: Build (Compilação e Instalação)
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instala via requirements.txt de forma isolada
RUN pip install --no-cache-dir -r requirements.txt


# Camada 2: Runtime (Execução Final)
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /usr/local /usr/local

# Copia os arquivos como estão na árvore do repositório
COPY app.py .
COPY requirements.txt .
COPY Contrato_interno.md .
COPY README.md .
COPY src/ ./src/
COPY infra/ ./infra/
COPY prompts_e_testes/ ./prompts_e_testes/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]