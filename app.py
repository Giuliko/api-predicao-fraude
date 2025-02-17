import streamlit as st
import requests
import pandas as pd
import time
import io

# Definir a URL da API
API_URL = "https://web-production-3f30f.up.railway.app"

# Configuração inicial da página
st.set_page_config(page_title="Predição de Fraude", layout="wide")

# Criar estado inicial da aba ativa
if "aba_atual" not in st.session_state:
    st.session_state["aba_atual"] = "Upload"

# Criar estado para armazenar a API Key
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

# Criar menu de navegação
aba_selecionada = st.radio("Navegação", ["🔼 Upload de Arquivo", "📊 Resultados"], 
                           index=0 if st.session_state["aba_atual"] == "Upload" else 1)

# 🌟 ABA 1: UPLOAD DO CSV
if aba_selecionada == "🔼 Upload de Arquivo":
    st.title("🔼 Enviar Arquivo CSV")

    # Campo para a API Key (armazenando no session_state)
    api_key = st.text_input("🔑 Digite sua API Key:", type="password")
    if api_key:
        st.session_state["api_key"] = api_key  # Salvar a API Key no estado global

    # Upload do arquivo CSV
    arquivo = st.file_uploader("📂 Escolha um arquivo CSV para enviar", type=["csv"])

    # Variável para exibir mensagem ao usuário
    if "mensagem_status" not in st.session_state:
        st.session_state["mensagem_status"] = ""

    if st.button("📊 Processar Arquivo"):
        if arquivo and st.session_state["api_key"]:
            with st.spinner("🔄 Processando arquivo... Isso pode levar alguns segundos..."):
                # Criar payload do arquivo
                files = {"file": (arquivo.name, arquivo, "text/csv")}
                headers = {"X-API-KEY": st.session_state["api_key"]}

                # Simula tempo de processamento
                time.sleep(2)

                # Enviar o arquivo para a API
                response = requests.post(f"{API_URL}/upload/", files=files, headers=headers)

                if response.status_code == 200:
                    st.success("✅ Arquivo enviado com sucesso!")
                    st.balloons()  # 🎈 Animação ao concluir o processo
                    st.session_state["arquivo_processado"] = True
                    st.session_state["mensagem_status"] = "✅ Processamento concluído! Acesse a aba '📊 Resultados' para visualizar ou baixar os dados."
                else:
                    st.session_state["mensagem_status"] = "❌ Erro ao enviar arquivo: " + response.json()["detail"]
        else:
            st.warning("⚠️ Por favor, insira a API Key e faça o upload de um arquivo.")

    # Exibir mensagem quando o arquivo estiver pronto
    if st.session_state["mensagem_status"]:
        st.info(st.session_state["mensagem_status"])

    # Botão para mudar para a aba de resultados
    if "arquivo_processado" in st.session_state:
        if st.button("📊 Ver Resultados"):
            st.session_state["aba_atual"] = "📊 Resultados"
            st.rerun()  # 🔄 Atualiza a UI para refletir a mudança imediatamente

# 🌟 ABA 2: RESULTADOS
if aba_selecionada == "📊 Resultados":
    st.title("📊 Visualizar Resultados")

    if "arquivo_processado" in st.session_state:
        with st.spinner("📥 Buscando os resultados... Aguarde..."):
            time.sleep(2)

            # Baixar o arquivo processado
            response = requests.get(f"{API_URL}/download/", headers={"X-API-KEY": st.session_state["api_key"]})

            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))

                st.success("✅ Resultados carregados com sucesso!")
                st.dataframe(df)

                # Botão de download
                st.download_button(
                    label="📥 Baixar Resultados",
                    data=response.content,
                    file_name="resultado_fraude.csv",
                    mime="text/csv"
                )
            else:
                st.error("❌ Erro ao buscar os resultados.")
    else:
        st.info("ℹ️ Nenhum arquivo processado ainda. Envie um CSV primeiro.")
