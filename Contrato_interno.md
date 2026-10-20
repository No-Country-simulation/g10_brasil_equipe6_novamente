# 🤝 Contrato de Integração (Frontend <-> Backend)

Para que todos possam programar em paralelo sem que o código quebre na hora da integração, precisamos decidir o formato de comunicação entre a Interface (Streamlit) e o Motor IA (RAG/Gemini). 

Vamos focar na seguinte opção arquiteturial.

---

O Streamlit importa os arquivos do backend como módulos Python comuns. Tudo roda no mesmo servidor e na mesma porta.
* **Vantagem:** Zero complexidade de rede, super rápido de implementar, sem erros de conexão.
* **Desvantagem:** O backend e a interface rodam acoplados.

**Contrato Esperado:**
O Streamlit fará a chamada exata assim no `app.py`:
```python
from src.rag import processar_documento
from src.llm import gerar_conteudo

# 1. Moab recebe o arquivo diretamente do Streamlit
sucesso = processar_documento(arquivo_bytes, "nome_do_arquivo.pdf")

# 2. Letícia recebe os parâmetros textuais
resultado_json = gerar_conteudo("nome_do_arquivo.pdf", "Iniciante", "Flashcards", "Geral")