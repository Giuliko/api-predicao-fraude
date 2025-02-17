import pandas as pd
from utils.NewDataProcess import new_data_process
import pickle
import os

# Definir caminhos relativos
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "data")
model_dir = os.path.join(base_dir, "model")
output_dir = os.path.join(base_dir, "output")

input_path = os.path.join(data_dir, "dados_coletados20k.csv")
modelo_path = os.path.join(model_dir, "random_forest_model.pkl")
output_path = os.path.join(output_dir, "resultados_predicao.csv")

# Criar diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Depuração: Verificar caminho dos arquivos
print(f"Caminho do arquivo CSV: {input_path}")
print(f"Caminho do modelo: {modelo_path}")
if not os.path.exists(input_path):
    raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")
if not os.path.exists(modelo_path):
    raise FileNotFoundError(f"Modelo não encontrado: {modelo_path}")

df_novos_dados = pd.read_csv(input_path)

# Armazenar a coluna "Contrato" separadamente
if "Contrato" in df_novos_dados.columns:
    df_contrato = df_novos_dados[["Contrato"]].copy()
else:
    raise ValueError("A coluna 'Contrato' não foi encontrada nos dados de entrada.")

# Processar os dados sem remover "Contrato"
df_pronto = new_data_process(df_novos_dados)

# Carregar o modelo salvo
with open(modelo_path, 'rb') as arquivo:
    modelo = pickle.load(arquivo)

# Realizar a previsão
predicoes = modelo.predict(df_pronto)

# Criar um DataFrame com os resultados
df_resultado = df_contrato.copy()
df_resultado["Predicao_Fraude"] = predicoes

# Salvar os resultados em um arquivo CSV
df_resultado.to_csv(output_path, index=False)

# Exibir os primeiros resultados
print(f"Resultados salvos em: {output_path}")
print(df_resultado.head())