from src.rag.document_loader import (
    DocumentLoadingError,
    extrair_diagramas_documento,
)
from src.rag.pipeline import RAGPipeline

# Cache em memória dos diagramas extraídos por nome de arquivo
_CACHE_DIAGRAMAS: dict[str, list[dict]] = {}


def processar_e_indexar_documento(arquivo_bytes: bytes, nome_arquivo: str) -> bool:
    """
    Adapter (Facade) que respeita o contrato da API,
    conectando o endpoint FastAPI à arquitetura orientada a objetos do RAG.
    """
    try:
        pipeline = RAGPipeline()
        resultado = pipeline.ingest(
            content=arquivo_bytes, 
            filename=nome_arquivo,
            document_id=nome_arquivo # <-- A MUDANÇA CRÍTICA AQUI (Amarra o ID ao nome do arquivo)
        )
        diagramas = extrair_diagramas_documento(arquivo_bytes, nome_arquivo)
        _CACHE_DIAGRAMAS[nome_arquivo] = diagramas
        print(
            f"[RAG] Sucesso: {resultado.chunk_count} chunks e "
            f"{len(diagramas)} diagramas extraídos de {nome_arquivo}"
        )
        return resultado.chunk_count > 0
    except (DocumentLoadingError, ValueError) as e:
        print(f"[RAG] Erro de validação/leitura do documento: {e}")
        raise
    except Exception as e:
        print(f"[RAG] Erro ao processar documento: {e}")
        return False


def recuperar_diagramas(nome_arquivo: str) -> list[dict]:
    """Retorna os diagramas técnicos extraídos do documento (se houver)."""
    return list(_CACHE_DIAGRAMAS.get(nome_arquivo, []))

def recuperar_contexto(query: str, nome_arquivo: str, k: int = 6) -> str:
    """
    Função exportada para a Letícia usar no llm.py.
    Busca no ChromaDB os trechos mais relevantes do arquivo e retorna como texto plano.
    """
    try:
        pipeline = RAGPipeline()
        # Busca os textos vinculados EXATAMENTE àquele PDF
        documentos_encontrados = pipeline.search(
            query=query, 
            document_id=nome_arquivo, 
            k=k
        )
        documentos_ordenados = sorted(
            documentos_encontrados,
            key=lambda doc: doc.metadata.get("chunk_index", 0),
        )
        
        contexto_concatenado = "\n\n".join([doc.page_content for doc in documentos_ordenados])
        return contexto_concatenado
        
    except Exception as e:
        print(f"[RAG] Erro ao recuperar contexto: {e}")
        return ""