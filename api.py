import json
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.rag import processar_e_indexar_documento
from src.llm import gerar_conteudo

app = FastAPI(title="NovaMente API")

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
    return {"status": "online", "service": "NovaMente API"}


@app.post("/api/adaptar")
def adaptar_conteudo(
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

    # Configura o ambiente dinamicamente conforme a escolha do frontend
    if "Local" in motor:
        os.environ["USE_LOCAL_LLM"] = "True"
        os.environ["OLLAMA_MODEL"] = modelo_local.strip() or "llama3.1:8b"
    else:
        os.environ["USE_LOCAL_LLM"] = "False"
        if apiKey and apiKey.strip():
            os.environ["GOOGLE_API_KEY"] = apiKey.strip()

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

    try:
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

    # Tenta guardar evidência no OCI Object Storage sem bloquear ou falhar a requisição caso o OCI esteja offline
    try:
        from src.storage import upload_bytes

        json_bytes = json.dumps(resposta, ensure_ascii=False, indent=2).encode("utf-8")
        nome_obj_nuvem = f"evidencia_{perfil.replace(' ', '')}_{formato.replace(' ', '')}.json"
        upload_bytes(nome_obj_nuvem, json_bytes, content_type="application/json")
    except Exception as e:
        print(f"[OCI] Aviso: conteúdo gerado, mas não foi possível salvar no Object Storage: {e}")

    return resposta


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
