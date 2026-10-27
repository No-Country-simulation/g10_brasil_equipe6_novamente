#src/llm.py - Conexão com o Gemini (Sprint 1, tarefa 1)

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


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


# TODO (tarefa 3): parser de saída em JSON
# TODO: gerar_conteudo


# Teste da tarefa 2
if __name__ == "__main__":
    chain = criar_chain_basica()
    resposta = chain.invoke({
        "texto": "Explique em 2 frases o que é RAG."
    })
    print(resposta)
