from src.rag.pipeline import RAGPipeline

def processar_e_indexar_documento(arquivo_bytes: bytes, nome_arquivo: str) -> bool:
    """
    Adapter (Facade) que respeita o contrato do Streamlit, 
    conectando a interface à arquitetura orientada a objetos.
    """
    try:
        pipeline = RAGPipeline()
        resultado = pipeline.ingest(
            content=arquivo_bytes, 
            filename=nome_arquivo,
            document_id=nome_arquivo # <-- A MUDANÇA CRÍTICA AQUI (Amarra o ID ao nome do arquivo)
        )
        print(f"[RAG] Sucesso: {resultado.chunk_count} chunks indexados do arquivo {nome_arquivo}")
        return resultado.chunk_count > 0
    except Exception as e:
        print(f"[RAG] Erro ao processar documento: {e}")
        return False

def recuperar_contexto(query: str, nome_arquivo: str) -> str:
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
            k=3 # Pega os 3 pedaços mais relevantes
        )
        
        contexto_concatenado = "\n\n".join([doc.page_content for doc in documentos_encontrados])
        return contexto_concatenado
        
    except Exception as e:
        print(f"[RAG] Erro ao recuperar contexto: {e}")
        return ""