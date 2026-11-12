#src/llm.py - Conexão com o Gemini (Sprint 1, tarefa 1)

import os
import json

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.exceptions import OutputParserException

# --- INCLUSÃO: Importando a função do Moab ---
from src.rag import recuperar_contexto 

load_dotenv()  


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI | ChatOllama:
    # Permite usar um modelo local sem alterar o fluxo padrão com Gemini.
    if os.getenv("USE_LOCAL_LLM", "False") == "True":
        return ChatOllama(model="qwen2.5:7b-instruct", temperature=temperature)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada. Configure no arquivo .env")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        google_api_key=api_key,
        temperature=temperature,
        max_retries=3,
    )

# (tarefa 2): criar a chain básica no LangChain

def criar_chain_basica():

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente educacional."),
        ("human", "{texto}"),
    ])
    return prompt | get_llm() | StrOutputParser()


# (tarefa 3): parser de saída em JSON
class Item(BaseModel):
    topico_ou_pergunta: str = Field(description="Tópico ou pergunta (flashcard/quiz)")
    explicacao_ou_resposta: str = Field(description="Explicação ou resposta correta")

class Metadados(BaseModel):
    perfil_aplicado: str
    formato_gerado: str
    tempo_estimado_estudo_minutos: int
    conceitos_chave: list[str]

class ConteudoAdaptado(BaseModel):
    titulo: str
    introducao_contextualizada: str
    itens: list[Item]

class SaidaLLM(BaseModel):
    metadados: Metadados
    conteudo_adaptado: ConteudoAdaptado

INSTRUCOES_FORMATO = {
    "Flashcards": "Cada item é um flashcard: pergunta curta e resposta direta.",
    "Quiz": "Cada item é uma questão de múltipla escolha: coloque a pergunta e as alternativas A, B, C e D em topico_ou_pergunta, e a letra correta com uma justificativa curta em explicacao_ou_resposta.",
    "Tutorial Passo a Passo": "Cada item é um passo numerado: o título do passo em topico_ou_pergunta e como executá-lo em explicacao_ou_resposta.",
    "Resumo Executivo": "Cada item é um ponto-chave: o tema em topico_ou_pergunta e uma explicação objetiva em explicacao_ou_resposta.",
}


def criar_chain_json():
    parser = JsonOutputParser(pydantic_object=SaidaLLM)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Você é um especialista em educação técnica. Adapte o conteúdo ao perfil, "
         "ao formato e ao nicho pedidos. Escreva em português. "
         "Responda APENAS com JSON válido, sem markdown e sem texto extra.\n\n"
         "Regra do formato: {instrucao_formato}\n\n"
         "{format_instructions}"),
        ("human",
         "Perfil: {perfil}\nFormato: {formato}\nNicho: {nicho}\n"
         "Documento: {nome_ficheiro}\n\nConteúdo-base:\n{contexto}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    return prompt | get_llm() | parser

# gerar_conteudo
def gerar_conteudo(nome_ficheiro: str, perfil: str, formato: str, nicho: str,
                   contexto: str | None = None) -> dict:
   
    if contexto is None:
        # --- INCLUSÃO: Integração Real com o RAG ---
        query_busca = f"Principais conceitos sobre {nicho} adequados para o perfil {perfil}"
        contexto_extraido = recuperar_contexto(query=query_busca, nome_arquivo=nome_ficheiro)
        contexto = contexto_extraido if contexto_extraido.strip() else "Informação não encontrada no documento."
        # -------------------------------------------

    try:
        bruto = criar_chain_json().invoke({
            "perfil": perfil,
            "formato": formato,
            "nicho": nicho,
            "nome_ficheiro": nome_ficheiro,
            "contexto": contexto,
            "instrucao_formato": INSTRUCOES_FORMATO.get(formato, "Organize em itens claros."),
        })
        saida = SaidaLLM.model_validate(bruto)  
    except (OutputParserException, ValidationError) as e:
        return {"status": "erro", "mensagem": f"O modelo não devolveu um JSON válido: {e}"}
    except Exception as e:  
        return {"status": "erro", "mensagem": f"Falha ao chamar o modelo: {e}"}

    resultado = {"status": "sucesso", **saida.model_dump()}
    resultado["metadados"]["perfil_aplicado"] = perfil
    resultado["metadados"]["formato_gerado"] = formato
    return resultado

# Teste da tarefa 3
if __name__ == "__main__":
    resultado = gerar_conteudo(
        "teste.pdf", "Iniciante", "Flashcards", "Geral",
        contexto="RAG combina busca em documentos com um modelo de linguagem "
                 "para gerar respostas mais confiáveis.",
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False))