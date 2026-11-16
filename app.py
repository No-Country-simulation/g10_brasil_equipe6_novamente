import json
import os
import urllib.request

import streamlit as st

# Integração Real: Substituindo o mock pelas funções do backend da equipa
from src.rag import processar_e_indexar_documento
from src.llm import gerar_conteudo
from src.storage import backup_directory, upload_bytes


@st.cache_data(ttl=60)
def obter_modelos_ollama():
    """Busca dinamicamente os modelos instalados no servidor Ollama local."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            dados = json.loads(response.read().decode("utf-8"))
            modelos = [modelo["name"] for modelo in dados.get("models", [])]
            return modelos if modelos else ["Nenhum modelo instalado"]
    except Exception:
        return ["llama3.1:8b", "qwen2.5:7b-instruct-q4_K_M"]


st.set_page_config(page_title="NovaMente MVP", layout="centered", page_icon="🧠")

with st.sidebar:
    st.header("⚙️ Motor de Inteligência Artificial")
    motor_escolhido = st.radio("Selecione o ambiente de processamento:", ["Nuvem (Google Gemini)", "Local (Ollama)"])
    
    if motor_escolhido == "Local (Ollama)":
        lista_modelos = obter_modelos_ollama()
        modelo_local = st.selectbox("Modelo Local:", lista_modelos)
        # Injeta as variáveis dinamicamente no sistema ANTES de chamar o LLM
        os.environ["USE_LOCAL_LLM"] = "True"
        os.environ["OLLAMA_MODEL"] = modelo_local
        st.success(f"Rodando offline com {modelo_local}")
    else:
        os.environ["USE_LOCAL_LLM"] = "False"
        st.info("A usar a API do Google Gemini")

st.title("🧠 NovaMente")
st.subheader("Adaptação Inteligente de Conteúdo Técnico")

with st.form("form_adaptacao"):
    st.markdown("**1. Envie o Documento Original**")
    ficheiro = st.file_uploader("Formatos suportados: PDF, MD, TXT", type=["pdf", "txt", "md"])
    
    st.markdown("**2. Configure a Adaptação**")
    col1, col2 = st.columns(2)
    with col1:
        perfil = st.selectbox("Perfil do Destinatário", [
            "Iniciante", 
            "Dev Júnior / Pleno", 
            "Líder Técnico / Arquiteto", 
            "Gestor / Executivo"
        ])
        formato = st.selectbox("Formato Pedagógico", [
            "Flashcards", 
            "Tutorial Passo a Passo", 
            "Quiz", 
            "Resumo Executivo"
        ])
    with col2:
        nicho = st.selectbox("Nicho de Aplicação", ["Geral", "Fintech", "Saúde", "E-commerce"])
    
    submit = st.form_submit_button("Gerar Conteúdo Educativo", type="primary")

if submit:
    if ficheiro is not None:
        if ficheiro.size == 0:
            st.error("O ficheiro enviado está vazio. Por favor, anexa um documento com texto.")
            st.stop()

        try:
            arquivo_bytes = ficheiro.read()
            nome_arquivo = ficheiro.name
            
            with st.spinner(f"A ler e indexar '{nome_arquivo}' no banco vetorial..."):
                try:
                    sucesso_rag = processar_e_indexar_documento(arquivo_bytes, nome_arquivo)
                except Exception as e:
                    st.error(f"Erro ao ler o documento. Pode ser um PDF digitalizado (sem texto) ou protegido. Detalhe: {e}")
                    st.stop()
                
            if not sucesso_rag:
                st.error("Falha ao indexar o documento. Verifica se o ficheiro possui texto legível.")
                st.stop()

            with st.spinner(f"A orquestrar IA para gerar {formato} focado em {nicho}... (pode demorar)"):
                resposta = gerar_conteudo(
                    nome_ficheiro=nome_arquivo, 
                    perfil=perfil, 
                    formato=formato, 
                    nicho=nicho
                )
            
            if resposta.get("status") == "sucesso":
                dados = resposta['conteudo_adaptado']
                meta = resposta['metadados']

                st.divider()
                st.markdown(f"### 🎯 {dados['titulo']}")
                st.info(f"**Tempo estimado:** {meta['tempo_estimado_estudo_minutos']} min | **Conceitos:** {', '.join(meta['conceitos_chave'])}")
                st.write(dados['introducao_contextualizada'])
                
                st.markdown("### 📚 Material de Estudo")
                for i, item in enumerate(dados['itens'], 1):
                    with st.expander(f"{i}. {item['topico_ou_pergunta']}"):
                        st.write(item['explicacao_ou_resposta'])

                st.toast('Conteúdo adaptado com sucesso!', icon='🎉')

                try:
                    with st.spinner("A guardar evidência e backup no Oracle Cloud (OCI)..."):
                        json_bytes = json.dumps(resposta, ensure_ascii=False, indent=2).encode('utf-8')
                        nome_obj_nuvem = f"evidencia_{perfil.replace(' ', '')}_{formato.replace(' ', '')}.json"
                        
                        upload_bytes(nome_obj_nuvem, json_bytes, content_type="application/json")
                        backup_directory()
                    st.toast(f'Evidência guardada no OCI: {nome_obj_nuvem}', icon='☁️')
                except Exception as e:
                    st.warning(f"O conteúdo foi gerado, mas falhou ao guardar no Oracle Cloud: {e}")
                        
            else:
                msg_erro = str(resposta.get('mensagem', ''))
                if "503" in msg_erro or "quota" in msg_erro.lower() or "429" in msg_erro:
                    st.error("⚠️ Os servidores do Google Gemini estão sobrecarregados ou a nossa cota gratuita estourou. Tenta novamente num minuto.")
                elif "não trouxe informação suficiente" in msg_erro:
                    st.warning("⚠️ O documento não possui informações suficientes para gerar conteúdo de qualidade e com rigor factual.")
                else:
                    st.error(f"❌ Erro na geração: {msg_erro}")

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado na aplicação: {str(e)}")
            
    else:
        st.warning("Por favor, anexa um documento técnico de origem.")