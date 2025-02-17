import os
import pickle
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from utils.NewDataProcess import new_data_process
from fastapi.responses import FileResponse
from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader

# Definir a chave de API esperada (poderíamos armazenar em uma variável de ambiente no Railway)
API_KEY = "meu_segredo_super_secreto"  # 🔒 Substitua por uma chave segura
api_key_header = APIKeyHeader(name="X-API-KEY")

# Função para verificar se a chave é válida
def verificar_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado. API Key inválida.")

# Criar a instância da API
app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API de Predição de Fraude está rodando! Acesse /docs para testar."}

# Definir caminhos relativos
base_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(base_dir, "model")
output_dir = os.path.join(base_dir, "output")
os.makedirs(output_dir, exist_ok=True)

# Caminho do modelo treinado
modelo_path = os.path.join(model_dir, "random_forest_model.pkl")

# Carregar o modelo de Machine Learning
with open(modelo_path, 'rb') as arquivo:
    modelo = pickle.load(arquivo)

@app.post("/upload/")
def upload_file(file: UploadFile = File(...), api_key: str = Security(verificar_api_key)):
    """
    Endpoint para upload de arquivo CSV e geração de previsões.
    """
    try:
        # Ler o arquivo CSV
        df_novos_dados = pd.read_csv(file.file)
        
        # Armazenar a coluna "Contrato" separadamente
        if "Contrato" in df_novos_dados.columns:
            df_contrato = df_novos_dados[["Contrato"]].copy()
        else:
            return {"erro": "A coluna 'Contrato' não foi encontrada no arquivo."}
        
        # Processar os dados
        df_pronto = new_data_process(df_novos_dados)
        
        # Fazer previsões
        predicoes = modelo.predict(df_pronto)
        
        # Criar DataFrame com os resultados
        df_resultado = df_contrato.copy()
        df_resultado["Predicao_Fraude"] = predicoes
        
        # Salvar arquivo com previsões
        output_path = os.path.join(output_dir, "resultados_predicao.csv")
        df_resultado.to_csv(output_path, index=False)
        
        return {"mensagem": "Previsão realizada com sucesso!", "arquivo_resultado": output_path}
    
    except Exception as e:
        return {"erro": str(e)}

@app.get("/download/")
def download_result():
    """
    Endpoint para baixar o arquivo CSV gerado.
    """
    output_path = os.path.join(output_dir, "resultados_predicao.csv")

    if not os.path.exists(output_path):
        return {"erro": "Arquivo não encontrado. Execute a predição primeiro."}

    return FileResponse(output_path, filename="resultados_predicao.csv", media_type="text/csv")

