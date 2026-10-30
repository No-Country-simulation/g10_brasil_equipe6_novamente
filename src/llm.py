#src/llm.py - Conexão com o Gemini (Sprint 1, tarefa 1)

import os
import json

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser


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


def criar_chain_json():
    parser = JsonOutputParser(pydantic_object=SaidaLLM)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Você é um especialista em educação técnica. Adapte o conteúdo ao perfil, "
         "ao formato e ao nicho pedidos. Escreva em português. "
         "Responda APENAS com JSON válido, sem markdown e sem texto extra.\n\n"
         "{format_instructions}"),
        ("human",
         "Perfil: {perfil}\nFormato: {formato}\nNicho: {nicho}\n"
         "Documento: {nome_ficheiro}\n\nConteúdo-base:\n{contexto}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    return prompt | get_llm() | parser

# TODO: gerar_conteudo


# Teste da tarefa 3
if __name__ == "__main__":
    chain = criar_chain_json()
    resultado = chain.invoke({
        "perfil": "Iniciante",
        "formato": "Flashcards",
        "nicho": "Geral",
        "nome_ficheiro": "teste.pdf",
        "contexto": "RAG é uma técnica que combina busca em uma base de documentos "
                    "com um modelo de linguagem para gerar respostas mais confiáveis.",
    })
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
