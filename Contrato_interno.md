# 🤝 Contrato de Integração (Frontend React <-> Backend FastAPI)

A comunicação entre a interface web em React (`frontend/`) e o motor de IA em Python (`api.py` + `src/`) é feita via API REST HTTP (`multipart/form-data`).

---

## 1. Endpoint da API (`api.py`)

- **Método e Rota:** `POST http://localhost:8000/api/adaptar`
- **Campos do `FormData` enviados pelo React:**
  - `file`: Arquivo original (`.pdf`, `.md`, `.txt`)
  - `perfil`: `"Iniciante"` | `"Dev Júnior / Pleno"` | `"Líder Técnico / Arquiteto"` | `"Gestor / Executivo"`
  - `formato`: `"Flashcards"` | `"Tutorial Passo a Passo"` | `"Quiz"` | `"Resumo Executivo"`
  - `nicho`: `"Geral"` | `"Fintech"` | `"Saúde"` | `"E-commerce"`
  - `motor`: `"Nuvem (Google Gemini)"` | `"Local (Ollama)"`
  - `modelo_local`: Nome do modelo local no Ollama (ex.: `"llama3.1:8b"`)
  - `apiKey`: Chave da API do Google Gemini quando o motor for em nuvem

---

## 2. Orquestração Interna no Backend Python

O `api.py` importa e aciona os módulos internos do pacote `src/`:

```python
from src.rag import processar_e_indexar_documento
from src.llm import gerar_conteudo

# 1. Indexa o documento enviado no ChromaDB
sucesso = processar_e_indexar_documento(arquivo_bytes, "nome_do_arquivo.pdf")

# 2. Recupera o contexto semântico e gera o conteúdo adaptado via Gemini ou Ollama
resultado_json = gerar_conteudo("nome_do_arquivo.pdf", "Iniciante", "Flashcards", "Geral")
```