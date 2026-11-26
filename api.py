from collections import defaultdict, deque
from contextlib import asynccontextmanager
import json
import os
import threading
import time
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=False)

DEFAULT_SERVER_GOOGLE_API_KEY = (
    os.getenv("GOOGLE_API_KEY", "").strip().strip('"').strip("'")
)
PREBUILT_RATE_LIMIT_MAX = int(os.getenv("PREBUILT_RATE_LIMIT_MAX", "10"))
PREBUILT_RATE_LIMIT_WINDOW_SEC = int(
    os.getenv("PREBUILT_RATE_LIMIT_WINDOW_SEC", "3600")
)

_LLM_ENV_LOCK = threading.Lock()
_RATE_LIMIT_LOCK = threading.Lock()
_PREBUILT_HITS: dict[str, deque[float]] = defaultdict(deque)


def _obter_ip_cliente(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _verificar_rate_limit_prebuilt(ip: str) -> None:
    if PREBUILT_RATE_LIMIT_MAX <= 0:
        return
    agora = time.time()
    limite_inicio = agora - PREBUILT_RATE_LIMIT_WINDOW_SEC
    with _RATE_LIMIT_LOCK:
        historico = _PREBUILT_HITS[ip]
        while historico and historico[0] < limite_inicio:
            historico.popleft()
        if len(historico) >= PREBUILT_RATE_LIMIT_MAX:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Limite gratuito da chave integrada atingido ({PREBUILT_RATE_LIMIT_MAX} gerações por hora). "
                    "Selecione 'Usar minha própria API Key' ou 'Local — Ollama' para continuar sem limites."
                ),
            )
        historico.append(agora)

from src.rag import processar_e_indexar_documento
from src.rag.embeddings import get_embeddings
from src.rag.vector_store import get_vector_store
from src.llm import (
    gerar_conteudo,
    preparar_prompts_rag,
    validar_e_formatar_saida_local,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Pré-carrega o modelo de embeddings e o ChromaDB na RAM do processo Uvicorn no boot
    try:
        get_embeddings()
        get_vector_store()
        print("[Startup] Modelo de embeddings e ChromaDB pré-carregados na memória.")
    except Exception as e:
        print(f"[Startup] Aviso ao pré-carregar embeddings: {e}")
    yield


app = FastAPI(title="NovaMente API", lifespan=lifespan)

# Libera o CORS para o React (localhost e Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "NovaMente API",
        "prebuilt_gemini_disponivel": bool(DEFAULT_SERVER_GOOGLE_API_KEY),
    }


def _salvar_evidencia_oci(resposta: dict, perfil: str, formato: str) -> None:
    """Guarda a evidência JSON diretamente no Bucket do OCI Object Storage após a geração."""
    try:
        from src.storage import upload_bytes

        json_bytes = json.dumps(resposta, ensure_ascii=False, indent=2).encode("utf-8")
        perfil_limpo = perfil.replace("/", "_").replace(" ", "")
        formato_limpo = formato.replace("/", "_").replace(" ", "")
        nome_obj_nuvem = f"evidencia_{perfil_limpo}_{formato_limpo}.json"
        upload_bytes(nome_obj_nuvem, json_bytes, content_type="application/json")
        print(f"[OCI] Evidência guardada com sucesso no bucket: {nome_obj_nuvem}")
    except Exception as e:
        print(f"[OCI] Aviso: conteúdo gerado, mas não foi possível salvar evidência no Object Storage: {e}")


@app.post("/api/preparar-rag")
def preparar_rag_para_ollama_local(
    file: UploadFile = File(...),
    perfil: str = Form(...),
    formato: str = Form(...),
    nicho: str = Form(...),
):
    """
    Etapa 1 do modo Local (Ollama no PC do visitante):
    Indexa o documento no ChromaDB da OCI e devolve o system_prompt + user_prompt
    para o navegador do visitante executar no http://localhost:11434 da própria máquina.
    """
    arquivo_bytes = file.file.read()
    if not arquivo_bytes:
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado está vazio. Por favor, anexe um documento com texto.",
        )

    nome_arquivo = (file.filename or "documento.txt").strip()
    try:
        sucesso_rag = processar_e_indexar_documento(arquivo_bytes, nome_arquivo)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Erro ao ler o documento. Pode ser um PDF digitalizado (sem texto) ou protegido. Detalhe: {e}",
        ) from e

    if not sucesso_rag:
        raise HTTPException(
            status_code=422,
            detail="Falha ao ler/indexar o documento. Verifique se o arquivo possui texto legível.",
        )

    return preparar_prompts_rag(
        nome_ficheiro=nome_arquivo,
        perfil=perfil,
        formato=formato,
        nicho=nicho,
    )


class FinalizarLocalRequest(BaseModel):
    nome_ficheiro: str
    perfil: str
    formato: str
    nicho: str = "Geral"
    resposta_bruta: str | dict
    usou_visao_local: bool = False


@app.post("/api/finalizar-local")
def finalizar_geracao_ollama_local(dados: FinalizarLocalRequest):
    """
    Etapa 2 do modo Local (Ollama no PC do visitante):
    Valida/normaliza o JSON gerado pelo Ollama do visitante e salva a evidência no Bucket da OCI.
    """
    resposta = validar_e_formatar_saida_local(
        resposta_bruta=dados.resposta_bruta,
        nome_ficheiro=dados.nome_ficheiro,
        perfil=dados.perfil,
        formato=dados.formato,
        usou_visao_local=dados.usou_visao_local,
    )
    if resposta.get("status") != "sucesso":
        msg_erro = str(resposta.get("mensagem", "Erro na validação da resposta do modelo local."))
        if "não trouxe informação suficiente" in msg_erro:
            raise HTTPException(
                status_code=422,
                detail="O documento não possui informações suficientes para gerar conteúdo com rigor factual.",
            )
        raise HTTPException(status_code=422, detail=msg_erro)

    _salvar_evidencia_oci(resposta, dados.perfil, dados.formato)
    return resposta


@app.post("/api/adaptar")
def adaptar_conteudo(
    request: Request,
    file: UploadFile = File(...),
    perfil: str = Form(...),
    formato: str = Form(...),
    nicho: str = Form(...),
    motor: str = Form(...),
    modelo_local: str = Form(default=""),
    apiKey: str = Form(default=""),
):
    arquivo_bytes = file.file.read()
    if not arquivo_bytes:
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado está vazio. Por favor, anexe um documento com texto.",
        )

    nome_arquivo = (file.filename or "documento.txt").strip()
    chave_usuario = (apiKey or "").strip()
    usando_local = "Local" in motor
    usando_prebuilt = (not usando_local) and (not chave_usuario)

    if usando_prebuilt:
        if not DEFAULT_SERVER_GOOGLE_API_KEY:
            raise HTTPException(
                status_code=503,
                detail=(
                    "A chave integrada do servidor não está configurada no momento. "
                    "Selecione 'Usar minha própria API Key' ou 'Local — Ollama'."
                ),
            )
        _verificar_rate_limit_prebuilt(_obter_ip_cliente(request))

    try:
        sucesso_rag = processar_e_indexar_documento(arquivo_bytes, nome_arquivo)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Erro ao ler o documento. Pode ser um PDF digitalizado (sem texto) ou protegido. Detalhe: {e}",
        ) from e

    if not sucesso_rag:
        raise HTTPException(
            status_code=422,
            detail="Falha ao ler/indexar o documento. Verifique se o arquivo possui texto legível.",
        )

    # Configura o ambiente de forma isolada para evitar que uma chave BYOK sobrescreva a chave padrão do servidor
    with _LLM_ENV_LOCK:
        chave_anterior = os.environ.get("GOOGLE_API_KEY")
        try:
            if usando_local:
                os.environ["USE_LOCAL_LLM"] = "True"
                os.environ["OLLAMA_MODEL"] = modelo_local.strip() or "llama3.1:8b"
            else:
                os.environ["USE_LOCAL_LLM"] = "False"
                os.environ["GOOGLE_API_KEY"] = (
                    chave_usuario if chave_usuario else DEFAULT_SERVER_GOOGLE_API_KEY
                )

            resposta = gerar_conteudo(
                nome_ficheiro=nome_arquivo,
                perfil=perfil,
                formato=formato,
                nicho=nicho,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ocorreu um erro inesperado ao gerar o conteúdo: {e}",
            ) from e
        finally:
            if DEFAULT_SERVER_GOOGLE_API_KEY:
                os.environ["GOOGLE_API_KEY"] = DEFAULT_SERVER_GOOGLE_API_KEY
            elif chave_anterior is not None:
                os.environ["GOOGLE_API_KEY"] = chave_anterior
            else:
                os.environ.pop("GOOGLE_API_KEY", None)

    if resposta.get("status") != "sucesso":
        msg_erro = str(resposta.get("mensagem", "Erro na geração."))
        if "503" in msg_erro or "quota" in msg_erro.lower() or "429" in msg_erro:
            raise HTTPException(
                status_code=503,
                detail="Os servidores do Google Gemini estão sobrecarregados ou a cota gratuita estourou. Tente novamente em instantes.",
            )
        if "não trouxe informação suficiente" in msg_erro:
            raise HTTPException(
                status_code=422,
                detail="O documento não possui informações suficientes para gerar conteúdo com rigor factual.",
            )
        raise HTTPException(status_code=500, detail=msg_erro)

    _salvar_evidencia_oci(resposta, perfil, formato)

    return resposta


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
