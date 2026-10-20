import streamlit as st

# Contrato Interno - Função Mock (Letícia e Moab vão substituir isto depois)
def gerar_conteudo_educacional_mock(nome_ficheiro, perfil, formato, nicho):
    return {
        "status": "sucesso",
        "metadados": {
            "perfil_aplicado": perfil,
            "formato_gerado": formato,
            "tempo_estimado_estudo_minutos": 10,
            "conceitos_chave": ["Exemplo 1", "Exemplo 2"]
        },
        "conteudo_adaptado": {
            "titulo": f"Dominando {nome_ficheiro} para {perfil}",
            "introducao_contextualizada": f"Uma visão focada no setor de {nicho}...",
            "itens": [
                {"topico_ou_pergunta": "O que é?", "explicacao_ou_resposta": "Explicação mockada aqui."}
            ]
        },
        "armazenamento_oci": {
            "bucket": "novamente-conteudos-educativos",
            "status_upload": "concluido"
        }
    }

st.set_page_config(page_title="NovaMente MVP", layout="centered")
st.title("🧠 NovaMente - Adaptação de Conteúdo")

with st.form("form_adaptacao"):
    ficheiro = st.file_uploader("Carregar Documento Técnico", type=["pdf", "txt", "md"])
    
    col1, col2 = st.columns(2)
    with col1:
        perfil = st.selectbox("Perfil do Destinatário", ["Iniciante", "Dev Júnior / Pleno", "Líder Técnico / Arquiteto", "Gestor / Executivo"])
        formato = st.selectbox("Formato Pedagógico", ["Flashcards", "Tutorial Passo a Passo", "Quiz", "Resumo Executivo"])
    with col2:
        nicho = st.selectbox("Nicho de Aplicação", ["Geral", "Fintech", "Saúde", "E-commerce"])
    
    submit = st.form_submit_button("Gerar Conteúdo Educativo")

if submit:
    if ficheiro is not None:
        with st.spinner("A processar pipeline RAG e a orquestrar LLM..."):
            # Aqui chamaremos a função real no futuro
            resposta = gerar_conteudo_educacional_mock(ficheiro.name, perfil, formato, nicho)
            st.success("Conteúdo adaptado com sucesso!")
            st.json(resposta)
    else:
        st.error("Por favor, anexa um documento técnico de origem.")