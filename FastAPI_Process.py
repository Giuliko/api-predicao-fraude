import os
import pickle
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from utils.NewDataProcess import new_data_process

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
def upload_file(file: UploadFile = File(...)):
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
