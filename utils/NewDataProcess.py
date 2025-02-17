import pandas as pd
import numpy as np

def new_data_process(df):
    """
    Pré-processa novos dados para garantir que estejam no formato correto para o modelo.
    """
    # Selecionar apenas as colunas necessárias
    colunas_necessarias = [
        "QT_Parcelas_Atraso", "QT_Total_Parcelas_Pagas", "QT_Dias_Atraso", 
        "Total_Pago", "Valor_Renda"
    ]
    
    # Verificar se todas as colunas estão presentes no novo dataset
    colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
    if colunas_faltantes:
        raise ValueError(f"Colunas ausentes no dataset de entrada: {colunas_faltantes}")
    
    # Filtrar apenas as colunas relevantes
    df = df[colunas_necessarias].copy()
    
    # Calcular as features derivadas
    df["Inadimplência"] = df["QT_Parcelas_Atraso"] / df["QT_Total_Parcelas_Pagas"]
    df["Comprometimento_Renda"] = df["Total_Pago"] / df["Valor_Renda"]
    df["Tempo_Médio_Atraso"] = df["QT_Dias_Atraso"] / df["QT_Parcelas_Atraso"]
    
    # Substituir valores infinitos por 0 (evitando erros na previsão)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    
    # Tratar valores ausentes
    df.fillna(0, inplace=True)
    
    # Selecionar as colunas finais para input do modelo
    colunas_finais = [
        "QT_Parcelas_Atraso", "QT_Total_Parcelas_Pagas", "Inadimplência", 
        "Comprometimento_Renda", "Tempo_Médio_Atraso", "QT_Dias_Atraso"
    ]
    
    return df[colunas_finais]

# Exemplo de uso com novos dados:
# df_novos_dados = pd.read_csv("novos_dados.csv")
# df_pronto = new_data_process(df_novos_dados)
# print(df_pronto.head())
