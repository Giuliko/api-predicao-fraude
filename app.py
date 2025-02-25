import streamlit as st
import requests
import pandas as pd
import time
import io

# Definir a URL da API
API_URL = "https://api-predicao-fraude-production.up.railway.app"
#API_URL = "http://127.0.0.1:8000"

# Configuração inicial da página
st.set_page_config(page_title="Predição de Fraude", layout="wide")

st.markdown(
    """
    <h1 style="color: #2d3357;">
        Nuvemshop
    </h1>
    """,
    unsafe_allow_html=True
)


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
            st.rerun()

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

                # 🏆 Cálculo de KPIs
                total_clientes = len(df)
                total_fraudes = df["Predicao_Fraude"].sum()
                percentual_fraude = (total_fraudes / total_clientes) * 100 if total_clientes > 0 else 0

                # 🔹 Calcular "Valor Total em Risco"
                valor_total_risco = df[df["Predicao_Fraude"] == 1]["Valor_Renda"].sum() if "Valor_Renda" in df.columns else "N/A"

                # 🔹 Calcular "Média de Dias de Atraso (Fraudadores)"
                media_atraso_fraudadores = df[df["Predicao_Fraude"] == 1]["QT_Dias_Atraso"].mean() if "QT_Dias_Atraso" in df.columns else "N/A"

                # 🔹 Encontrar "Faixa Salarial Mais Comum (Fraudadores)"
                faixa_salarial_mais_comum = (
                    df[df["Predicao_Fraude"] == 1]["Valor_Renda"].mode()[0]
                    if "Valor_Renda" in df.columns and not df[df["Predicao_Fraude"] == 1]["Valor_Renda"].empty
                    else "N/A"
                )

                # Exibir os KPIs
                st.markdown("### 📊 Métricas Principais")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Clientes Analisados", total_clientes)
                col2.metric("Total de Fraudes Detectadas", total_fraudes)
                col3.metric("Percentual de Fraude", f"{percentual_fraude:.2f}%")

                col4, col5, col6 = st.columns(3)
                col4.metric("Valor Total em Risco", f"R$ {valor_total_risco / 1_000_000:.2f} Mi" if valor_total_risco != "N/A" else "N/A")
                col5.metric("Média de Dias de Atraso (Fraudadores)", f"{media_atraso_fraudadores:.1f}" if media_atraso_fraudadores != "N/A" else "N/A")
                col6.metric("Faixa Salarial Mais Comum (Fraudadores)", f"R$ {faixa_salarial_mais_comum / 1_000:.2f}K" if faixa_salarial_mais_comum != "N/A" else "N/A")

                # Exibir DataFrame dos resultados
                st.markdown("### 📋 Detalhes dos Clientes Preditos")
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
