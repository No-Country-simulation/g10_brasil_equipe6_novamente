# 🎓 NovaMente

### Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional

**Hackathon ONE G10 — Oracle Next Education & Alura**

> **Status do projeto:** Em desenvolvimento ativo 🚀. A stack tecnológica e a arquitetura foram definidas e a equipe está focada na implementação do MVP.

## 📖 Sobre o projeto

O **NovaMente** é uma solução de tecnologia educacional (EdTech) que tem como objetivo transformar documentações técnicas, manuais de software, artigos e bases de conhecimento em conteúdos educacionais personalizados, utilizando **Inteligência Artificial Generativa, Retrieval-Augmented Generation (RAG) e orquestração com LangChain**.

A proposta é facilitar o aprendizado de conteúdos técnicos complexos, adaptando a linguagem, a profundidade e a estrutura pedagógica de acordo com o perfil do destinatário, o contexto de aplicação e o formato de aprendizagem desejado.

O projeto está sendo desenvolvido no contexto do **Hackathon do Programa Oracle Next Education (ONE) — Grupo 10**, em parceria com a Alura.

## 🚀 Objetivo do MVP

Desenvolver um **Produto Mínimo Viável (MVP)** 100% em Python, capaz de:

1. Receber e processar documentos técnicos nos formatos PDF, Markdown ou texto via interface Streamlit.
2. Extrair, segmentar e indexar o conteúdo utilizando RAG (ChromaDB).
3. Utilizar o modelo Google Gemini (via LangChain) para adaptar materiais aos perfis e formatos solicitados.
4. Gerar conteúdos educacionais estruturados rigorosamente em JSON.
5. Persistir os documentos originais, os embeddings (índices vetoriais) e os conteúdos gerados no **Oracle Cloud Infrastructure (OCI) Object Storage**, utilizando a camada Always Free.
6. Realizar o deploy da aplicação em um container Docker hospedado em uma **OCI Compute (VM)**.

## 🛠️ Stack Tecnológica Definida

Nossa equipe optou por uma arquitetura unificada e simplificada, focada em Python, para garantir velocidade de entrega e evitar gargalos de integração entre front-end e back-end. **Não utilizaremos bancos de dados relacionais.**

| Categoria | Tecnologias Definidas |
|---|---|
| **Linguagem Base** | Python 3 |
| **Interface (UI)** | Streamlit |
| **Orquestração IA** | LangChain |
| **LLM Principal** | Google Gemini |
| **RAG / Vector Store** | ChromaDB (índice local persistido em nuvem) |
| **Processamento PDF** | PyPDF |
| **Armazenamento** | OCI Object Storage (Documentos, JSONs e backup dos Embeddings) |
| **Infraestrutura / Deploy** | Docker + OCI Compute (VM Always Free) |

## 🧠 Arquitetura e Fluxo de Dados

A solução é organizada em um fluxo de processamento direto acionado pela interface do usuário:

```mermaid
flowchart TD
    UI["Interface (Streamlit)"] -->|Upload PDF/TXT| RAG["Módulo RAG (ChromaDB)"]
    UI -->|Parâmetros (Perfil, Formato)| ORQ["Módulo IA (LangChain)"]
    
    RAG -->|Chunks Relevantes| ORQ
    ORQ -->|Prompt + Contexto| LLM["Google Gemini"]
    LLM -->|Resposta Estruturada| ORQ
    
    ORQ -->|JSON Validado| UI
    
    RAG -.->|Backup do Índice| OCI[("OCI Object Storage")]
    UI -.->|Salva Original e JSON| OCI
```

## 📂 Estrutura do Repositório

Para evitar conflitos de merge (já que todos somos iniciantes e o time tem forte viés de backend), adotamos uma estrutura plana ("flat"). Cada arquivo principal tem um "dono" responsável por sua manutenção durante o hackathon.

```text
novamente-mvp/
├── app.py                 # Interface principal no Streamlit.
├── requirements.txt       # Dependências do projeto (streamlit, langchain, etc).
├── .env.example           # Template de variáveis de ambiente (nunca commitar o .env real!).
├── .gitignore             # Bloqueios de arquivos sensíveis e cache.
├── Dockerfile             # Script de conteinerização para deploy na OCI.
├── README.md              # Documentação oficial do projeto.
├── src/                   # Motor do Backend
│   ├── rag.py             # Pipeline de ingestão, chunking e ChromaDB.
│   ├── llm.py             # Orquestração de chains LangChain e conexão com Gemini.
│   └── storage.py         # Integração com OCI SDK (Object Storage).
└── prompts_e_testes/      # Validação de prompts e exemplos de JSON estruturado.
```

## ⚙️ Instalação e Execução Local

Siga os passos abaixo para rodar a aplicação na sua máquina durante o desenvolvimento:

1. **Clone o repositório:**
   ```bash
   git clone git@github.com:No-Country-simulation/g10_brasil_equipe6_novamente.git
   cd novamente-mvp
   ```

2. **Crie e ative um ambiente virtual (Recomendado):**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuração de Variáveis de Ambiente:**
   Copie o arquivo `.env.example` para um novo arquivo chamado `.env` e preencha com suas chaves de API locais (Gemini API Key, OCI Config). **Atenção: O arquivo `.env` já está no `.gitignore` para sua segurança.**

5. **Execute a aplicação Streamlit:**
   ```bash
   streamlit run app.py
   ```
   A interface abrirá automaticamente no seu navegador no endereço `http://localhost:8501`.

## 🤝 Regras de Contribuição da Equipe

1. **Nunca suba chaves de API:** Verifique sempre se o seu `.env` não está sendo enviado no commit.
2. **Trabalhe na sua Branch:** Crie ramificações para suas tarefas (ex: `feat-moab-rag`, `feat-leticia-gemini`).
3. **Respeite o escopo dos arquivos:** Edite preferencialmente os arquivos designados à sua frente de trabalho (`rag.py`, `llm.py`, `storage.py`, `app.py`) para minimizar conflitos na hora de juntar (merge) o código na branch `main`.

---
*Projeto desenvolvido para o Hackathon ONE G10 — Oracle Next Education & Alura*