#src/llm.py - Conexão com o Gemini (Sprint 1, tarefa 1)

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  


def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
   
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada. Configure no arquivo .env")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        google_api_key=api_key,
        temperature=temperature,
    )


# TODO (tarefa 2): criar a chain básica no LangChain
# TODO (tarefa 3): parser de saída em JSON
# TODO: gerar_conteudo

 # Teste rápido da conexão: python src/llm.py
if __name__ == "__main__":
   
    llm = get_llm()
    resposta = llm.invoke("Diga olá em uma frase curta.")
    print(resposta.text)