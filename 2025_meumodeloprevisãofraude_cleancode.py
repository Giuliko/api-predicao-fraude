# -*- coding: utf-8 -*-
"""2025_MeuModeloPrevisãoFraude_CleanCode.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/11OfTIl94kMaFZmTuVhyeOZyPjutUOiPT
"""

import pandas as pd
import warnings
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np
from xgboost import XGBClassifier
# from imblearn import under_sampling, over_sampling
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import cross_val_score

warnings.filterwarnings("ignore")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.options.display.float_format = '{:.2f}'.format # configuração para não ficar em notação científica

# Carregar os dados
file_path = "C:/Users/giuli/Documents/Analytics/Análise Fraude/dados_coletados10k.csv"
df = pd.read_csv(file_path)

# Exibir as primeiras linhas do dataframe para inspeção inicial
df.head()

# Verificar informações gerais do dataset
df.info()

# Verificar a presença de valores ausentes
missing_values = df.isnull().sum()
missing_values_percentage = (missing_values / len(df)) * 100

# Criar um dataframe com a contagem e percentual de valores ausentes
missing_df = pd.DataFrame({
    "[Coluna]": missing_values.index,
    "[Valores Ausentes]": missing_values.values,
    "[% Valores Ausentes]": missing_values_percentage.values
})

missing_df

# Verificar a distribuição das variáveis numéricas
numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
numeric_summary = df[numeric_columns].describe()

numeric_summary

# Verificar a distribuição das variáveis categóricas
categorical_columns = df.select_dtypes(include=['object']).columns

categorical_summary = {}
for col in categorical_columns:
    categorical_summary[col] = df[col].value_counts()

dataframe=pd.DataFrame(categorical_summary)

dataframe

# APÓS ANALISE INICIAL QUE REALIZAMOS ACIMA, ENTENDEMOSO QUE ALGUMAS VARIÁVEIS NÃO POSSUEM RELEVANCIA.

#  Contrato --> Essa variável é a identificação de cada cliente
#  Data_Contratacao, VL_Patrimonio, Possui_Patrimonio, Escolaridade --> Essas não irão ter relevancia no modelo

# Remover as colunas especificadas
columns_to_drop = ["Contrato", "Data_Contratacao", "Escolaridade", "Possui_Patrimonio", "VL_Patrimonio"]
df = df.drop(columns=columns_to_drop)

df.head()

# Substituir valores ausentes em QT_Dias_Atraso pela mediana, pois é menos sensível a outliers
df["QT_Dias_Atraso"] = df["QT_Dias_Atraso"].fillna(df["QT_Dias_Atraso"].median())
df.head()

# Vamos constatar que realmente não há valores nulos
df.isnull().sum()

#Aqui vamos realizar a engenharia de features - nada mais é do que a criação de novas colunas baseadas nos dados que já existem na base. Essa criação pode ser de métricas novas, realizando cálculos com as colunas existentes ou agrupamento de variáveis categóricas etc. \"""

# Criando as novas colunas no dataframe
df_transformed = df

# 1️⃣ Relação Renda/Empréstimo
df_transformed["Relação_Renda_Emprestimo"] = df_transformed["VL_Emprestimo"] / df_transformed["Valor_Renda"]

# 2️⃣ Relação Parcelas Pagas
df_transformed["Relação_Parcelas_Pagas"] = df_transformed["QT_Total_Parcelas_Pagas"] / df_transformed["Prazo_Emprestimo"]

# 3️⃣ Inadimplência
df_transformed["Inadimplência"] = df_transformed["QT_Parcelas_Atraso"] / df_transformed["QT_Total_Parcelas_Pagas"]
df_transformed["Inadimplência"].fillna(0, inplace=True)  # Evitar NaNs quando não há parcelas pagas

# 4️⃣ Duração Restante Proporcional
df_transformed["Duração_Restante_Proporcional"] = df_transformed["Prazo_Restante"] / df_transformed["Prazo_Emprestimo"]

# 5️⃣ Relação Juros/Empréstimo
df_transformed["Relação_Juros_Emprestimo"] = df_transformed["Perc_Juros"] * df_transformed["VL_Emprestimo"]

# 6️⃣ Comprometimento da Renda
df_transformed["Comprometimento_Renda"] = df_transformed["Total_Pago"] / df_transformed["Valor_Renda"]

# 7️⃣ Tempo Médio de Atraso
df_transformed["Tempo_Médio_Atraso"] = df_transformed["QT_Dias_Atraso"] / df_transformed["QT_Parcelas_Atraso"]
df_transformed["Tempo_Médio_Atraso"].fillna(0, inplace=True)  # Evitar NaNs quando não há atraso

# 8️⃣ Histórico de Renegociação
df_transformed["Histórico_Renegociação"] = df_transformed["Qt_Renegociacao"] / df_transformed["QT_Total_Parcelas_Pagas"]
df_transformed["Histórico_Renegociação"].fillna(0, inplace=True)  # Evitar NaNs quando não há renegociação

# 9️⃣ Faixa_Prazo_Restante
df_transformed["Faixa_Prazo_Restante"] = pd.cut(
    df_transformed["Prazo_Restante"],
    bins=[-0.1, 0, 24, 60, 120, float("inf")],  # Incluindo -0.1 para capturar 0 corretamente
    labels=["Quitado", "Curto prazo", "Médio prazo", "Longo prazo", "Muito longo prazo"]
)

# 🔟 Faixa_Salarial
df_transformed["Faixa_Salarial"] = pd.cut(
    df_transformed["Valor_Renda"],
    bins=[0, 2500, 5000, 10000, 20000, float("inf")],
    labels=["Baixa renda", "Classe média baixa", "Classe média", "Classe média alta", "Alta renda"]
)

# 1️⃣1️⃣ Faixa_Prazo_Emprestimo
df_transformed["Faixa_Prazo_Emprestimo"] = pd.cut(
    df_transformed["Prazo_Emprestimo"],
    bins=[0, 24, 60, 120, float("inf")],
    labels=["Curto prazo", "Médio prazo", "Longo prazo", "Muito longo prazo"]
)

# 1️⃣2️⃣ Faixa_Etaria
df_transformed["Faixa_Etaria"] = pd.cut(
    df_transformed["Idade"],
    bins=[0, 25, 40, 60, float("inf")],
    labels=["Jovem", "Adulto jovem", "Meia-idade", "Idoso"]
)

# 1️⃣3️⃣ Faixa_Dias_Atraso
df_transformed["Faixa_Dias_Atraso"] = pd.cut(
    df_transformed["QT_Dias_Atraso"],
    bins=[-1, 0, 30, 90, 180, float("inf")],  # -1 para incluir zero
    labels=["Sem atraso", "Atraso leve", "Atraso moderado", "Atraso grave", "Atraso crítico"]
)

# Vamos constatar que realmente não há valores nulos
df_transformed.isnull().sum()

df_transformed.head()

"""
Minha recomendação é manter as colunas originais por enquanto, pelos seguintes motivos:

1️ Evitar perda de informações úteis
Algumas colunas originais podem conter informações que ainda são relevantes para o modelo, mesmo que tenham sido utilizadas para criar novas features.
Exemplo: "Valor_Renda" foi usada para criar "Relação_Renda_Emprestimo" e "Comprometimento_Renda", mas pode ser útil isoladamente para algumas técnicas de modelagem.
2️ Permitir análise de impacto das novas features
Manter as colunas originais nos permite comparar o desempenho das novas features no modelo.
Podemos fazer testes de importância das variáveis para verificar quais realmente agregam valor.
3️ Evitar viés de engenharia prematura
Nem sempre novas features são melhores do que os dados brutos. Algumas combinações podem não ter tanto impacto no modelo.
Remover colunas agora pode restringir as possibilidades de ajuste fino na modelagem.
4️ Impacto nos algoritmos de Machine Learning
Algoritmos como árvores de decisão e redes neurais podem se beneficiar de múltiplas representações dos dados.
Por outro lado, algoritmos como regressão logística e SVMs podem sofrer com multicolinearidade se houver redundância demais.
Quando remover as colunas originais?
Se após uma análise de correlação e importância das variáveis percebermos que algumas colunas originais não agregam valor ao modelo (ou geram multicolinearidade), podemos removê-las.

Sugestão: Antes de descartar qualquer coluna, rodamos uma análise de feature importance com algoritmos como Random Forest ou XGBoost.

Conclusão:
➡ Por enquanto, mantemos as colunas originais. 🔥
➡ Depois da análise de importância das variáveis, decidimos quais descartar.
"""

# Remover colunas categóricas para o modelo inicial
categorical_columns = ["Sexo", "UF_Cliente", "Estado_Civil", "Faixa_Prazo_Restante", "Faixa_Salarial",
                       "Faixa_Prazo_Emprestimo", "Faixa_Etaria", "Faixa_Dias_Atraso"]

# Criar cópia do dataframe para transformação
# df_model = df_transformed

# Transformar colunas categóricas em valores numéricos usando Label Encoding
label_encoders = {}
for col in categorical_columns:
    le = LabelEncoder()
    df_transformed[col] = le.fit_transform(df_transformed[col])
    label_encoders[col] = le  # Armazena o encoder caso precise ser revertido depois

# Tratar valores infinitos na coluna Tempo_Médio_Atraso
df_transformed["Tempo_Médio_Atraso"] = df_transformed["Tempo_Médio_Atraso"].replace([np.inf, -np.inf], np.nan)
df_transformed["Tempo_Médio_Atraso"] = df_transformed["Tempo_Médio_Atraso"].fillna(df_transformed["Tempo_Médio_Atraso"].median())

# Vamos constatar que realmente não há valores nulos
df_transformed.isnull().sum()

"""Dividir os dados em treino e teste para rodarmos os algoritmos. Nessa etapa ainda não vamos fazer previsões, vamos utilizar os algoritmos para nos mostrar quais são as colunas mais relevantes da base de dados."""

# Definir variáveis independentes (X) e variável alvo (y)
X = df_transformed.drop(columns=["Possivel_Fraude"])  # Features
y = LabelEncoder().fit_transform(df_transformed["Possivel_Fraude"])  # Variável alvo

# Verificar novamente se há valores infinitos ou extremamente grandes
problematic_values = X[(X == np.inf) | (X == -np.inf) | (X > np.finfo(np.float32).max)].any()

# Criar um relatório das colunas problemáticas
problematic_values_df = pd.DataFrame(problematic_values, columns=["Possui Problema"])
problematic_values_df = problematic_values_df[problematic_values_df["Possui Problema"]]

problematic_values_df

# Substituir valores infinitos por 0 nas colunas Inadimplência e Histórico_Renegociação
X["Inadimplência"] = X["Inadimplência"].replace([np.inf, -np.inf], 0)
X["Histórico_Renegociação"] = X["Histórico_Renegociação"].replace([np.inf, -np.inf], 0)

# Dividir os dados em treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Treinar o modelo Random Forest para análise de importância das features
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Obter importância das features
feature_importances = pd.DataFrame({"Feature": X.columns, "Importance": rf_model.feature_importances_})
feature_importances = feature_importances.sort_values(by="Importance", ascending=False)

feature_importances

# Agora vamos rodar o XGBoost para avaliar também as colunas mais relevantes em comparação com o random forest.\"""

# Ajustar o modelo XGBoost para execução mais eficiente
xgb_model = XGBClassifier(
    n_estimators=50,  # Reduzindo o número de árvores
    use_label_encoder=False,
    eval_metric='logloss',
    tree_method='hist',  # Método mais eficiente
    random_state=42
)

# Treinar o modelo XGBoost novamente
xgb_model.fit(X_train, y_train)

# Obter importância das features do XGBoost
xgb_feature_importances = pd.DataFrame({"Feature": X.columns, "Importance": xgb_model.feature_importances_})
xgb_feature_importances = xgb_feature_importances.sort_values(by="Importance", ascending=False)

xgb_feature_importances

"""📊 Comparação dos Modelos
🔹 Random Forest (Top 5 Features)

1️⃣ QT_Parcelas_Atraso → 26.47%

2️⃣ Inadimplência → 18.39%

3️⃣ QT_Total_Parcelas_Pagas → 16.15%

4️⃣ Relação_Parcelas_Pagas → 9.34%

5️⃣ Comprometimento_Renda → 6.21%

🔹 XGBoost (Top 5 Features)

1️⃣ QT_Parcelas_Atraso → 86% ✅ (extremamente relevante para XGBoost)

2️⃣ Qt_Renegociacao → 2%

3️⃣ Tempo_Médio_Atraso → 2%

4️⃣ Comprometimento_Renda → 1%

5️⃣ QT_Dias_Atraso → 1%

Agora precisamos decidir quais features devemos manter e quais podemos remover. Com base nos resultados, minha sugestão:

✅ Manter as features mais relevantes nos dois modelos:

1.   QT_Parcelas_Atraso (Ambos os modelos)
2.   QT_Total_Parcelas_Pagas (Random Forest)
3.   Inadimplência (Random Forest)
4.   Comprometimento_Renda (Ambos os modelos)
5.   Tempo_Médio_Atraso (XGBoost)
6.   QT_Dias_Atraso (XGBoost)

❌ Remover as features que tiveram importância zero no XGBoost e baixa relevância no Random Forest:

Idade, Sexo, Estado_Civil
UF_Cliente
Prazo_Emprestimo, Prazo_Restante
VL_Emprestimo, VL_Emprestimo_ComJuros
Faixa_Etaria, Faixa_Salarial, Faixa_Prazo_Restante, Faixa_Prazo_Emprestimo, Faixa_Dias_Atraso
Relação_Renda_Emprestimo, Relação_Juros_Emprestimo, Histórico_Renegociação, Duração_Restante_Proporcional

Devemos normalizar os dados antes da análise de importância das features?
Para Árvores de Decisão (Random Forest e XGBoost)

❌ Não é necessário

Esses algoritmos são baseados em divisões sucessivas dos dados e não são sensíveis a escalas.
Como eles usam apenas ordem relativa dos valores, não é necessário normalizar antes da análise de feature importance.
Para Modelos Baseados em Distâncias (Regressão Logística, SVM, Redes Neurais, KNN)

✅ É necessário

Esses modelos usam cálculos baseados em distâncias euclidianas, que podem ser distorcidos se os dados estiverem em escalas diferentes.
Exemplo: Se "Valor_Renda" varia entre R$1.000 e R$50.000, mas "Inadimplência" está entre 0 e 1, o modelo pode atribuir mais peso à renda simplesmente porque tem números maiores.
"""

# Lista das colunas a serem mantidas com base na análise de importância das features
columns_to_keep = [
    "QT_Parcelas_Atraso", "QT_Total_Parcelas_Pagas", "Inadimplência",
    "Comprometimento_Renda", "Tempo_Médio_Atraso", "QT_Dias_Atraso"
]

# Criar um novo dataframe apenas com as colunas relevantes
df_transformed_reduced = df_transformed[columns_to_keep + ["Possivel_Fraude"]]  # Mantendo a variável alvo

df_transformed_reduced.head()

# Verificar a presença de valores NaN e infinitos no dataset reduzido
nan_counts = df_transformed_reduced.isna().sum()
inf_counts = (df_transformed_reduced == np.inf).sum()

# Criar um relatório dos problemas encontrados
validation_report = pd.DataFrame({
    "Coluna": df_transformed_reduced.columns,
    "Valores NaN": nan_counts.values,
    "Valores Infinitos": inf_counts.values
})

validation_report

# Substituir valores infinitos por 0 em 'Inadimplência'
df_transformed_reduced["Inadimplência"] = df_transformed_reduced["Inadimplência"].replace([np.inf, -np.inf], 0)

# Verificar a presença de valores NaN e infinitos no dataset reduzido
nan_counts = df_transformed_reduced.isna().sum()
inf_counts = (df_transformed_reduced == np.inf).sum()

# Criar um relatório dos problemas encontrados
validation_report = pd.DataFrame({
    "Coluna": df_transformed_reduced.columns,
    "Valores NaN": nan_counts.values,
    "Valores Infinitos": inf_counts.values
})

validation_report

# Verificar o balanceamento da variável alvo (Possível Fraude)
target_distribution = df_transformed_reduced["Possivel_Fraude"].value_counts(normalize=True) * 100

# Criar um dataframe com a distribuição das classes
target_balance_df = pd.DataFrame({
    "Classe": target_distribution.index,
    "Percentual (%)": target_distribution.values
})

target_balance_df

# Separar as features (X) e a variável alvo (y)
X_smote = df_transformed_reduced.drop(columns=["Possivel_Fraude"])
y_smote = df_transformed_reduced["Possivel_Fraude"]

# Aplicar Label Encoding na variável alvo para o SMOTE funcionar corretamente
y_smote_encoded = LabelEncoder().fit_transform(y_smote)

# Aplicar o SMOTE para balanceamento das classes
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_smote, y_smote_encoded)

# Criar um novo dataframe com os dados balanceados
df_trans_balanced = pd.DataFrame(X_resampled, columns=X_smote.columns)
df_trans_balanced["Possivel_Fraude"] = y_resampled  # Adicionar a variável alvo de volta

# Exibir a nova distribuição da variável alvo após o SMOTE
balanced_target_distribution = pd.DataFrame({
    "Classe": ["Não", "Sim"],
    "Quantidade": [sum(y_resampled == 0), sum(y_resampled == 1)]
})

balanced_target_distribution

"""Nessa etapa já tratamos as colunas com valores nulos e vazios, já criamos novas colunas, já selecionamos as colunas mais relevantes pro modelo, já balanceamos a variável alvo. Agora vamos buscar quais são os melhores valores para os hyperparametros de cada modelo a ser testado. No nosso caso, testaremos o Random Forest e o XGBoost."""

# Definir os hiperparâmetros para Random Forest
param_grid_rf = {
    "n_estimators": [50, 100, 200],
    "max_depth": [None, 10, 20, 30],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4]
}

# Criar o modelo Random Forest
rf_model = RandomForestClassifier(random_state=42)

# Aplicar GridSearchCV
grid_search_rf = GridSearchCV(
    rf_model, param_grid_rf, cv=5, scoring="accuracy", n_jobs=-1, verbose=1
)

# Treinar o GridSearchCV com os dados balanceados
# X_resampled = X_train + dados ficticios; O mesmo vale para y_resampled
grid_search_rf.fit(X_resampled, y_resampled)

treinos_rf = pd.DataFrame(grid_search_rf.cv_results_)

# Acurácia em Treino
print(f"Acurácia em Treinamento: {grid_search_rf.best_score_ :.2%}")
print("")
print(f"Hiperparâmetros Ideais: {grid_search_rf.best_params_}")
print("")
print("Numero de treinamentos realizados: ", treinos_rf.shape[0])

# Definir os hiperparâmetros para XGBoost
param_grid_xgb = {
    "n_estimators": [50, 100, 200],
    "max_depth": [3, 6, 9],
    "learning_rate": [0.01, 0.1, 0.3],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0]
}

# Criar o modelo XGBoost
xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)

# Aplicar GridSearchCV para XGBoost
grid_search_xgb = GridSearchCV(
    xgb_model, param_grid_xgb, cv=5, scoring="accuracy", n_jobs=-1, verbose=1
)

# Treinar o GridSearchCV com os dados balanceados
# X_resampled = X_train + dados ficticios; O mesmo vale para y_resampled
grid_search_xgb.fit(X_resampled, y_resampled)

treinos_xgb = pd.DataFrame(grid_search_xgb.cv_results_)

# Acurácia em Treino
print(f"Acurácia em Treinamento: {grid_search_xgb.best_score_ :.2%}")
print("")
print(f"Hiperparâmetros Ideais: {grid_search_xgb.best_params_}")
print("")
print("Numero de treinamentos realizados: ", treinos_xgb.shape[0])

"""Agora que temos os melhores valores para os hyperparametros de cada modelo, vamos criá-los usando esses valores e testá-los na base de teste.

Antes precisamos garantir que a base de testes está correta, ou seja, contém somente as colunas mais relevantes e não possui NAs, Vazios ou valores infinitos.
"""

X_test.head()

columns_to_keep

# Garantir que X_test e y_test estão definidos corretamente
X_test = X_test[columns_to_keep]

X_test.head()

# Verificar novamente se há valores infinitos ou extremamente grandes
problematic_values = X_test[(X_test == np.inf) | (X_test == -np.inf) | (X_test > np.finfo(np.float32).max)].any()

# Criar um relatório das colunas problemáticas
problematic_values_df = pd.DataFrame(problematic_values, columns=["Possui Problema"])
problematic_values_df = problematic_values_df[problematic_values_df["Possui Problema"]]

problematic_values_df

y_test

# Criar o modelo Random Forest com os melhores hiperparâmetros encontrados
rf_best_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=4,
    min_samples_split=2,
    random_state=42
)

# Treinar o modelo Random Forest nos dados balanceados
rf_best_model.fit(X_resampled, y_resampled)

# Fazer previsões no conjunto de teste
y_pred_rf = rf_best_model.predict(X_test)

# Calcular métricas de avaliação para Random Forest
rf_metrics = {
    "Acurácia": accuracy_score(y_test, y_pred_rf),
    "Precisão": precision_score(y_test, y_pred_rf),
    "Recall": recall_score(y_test, y_pred_rf),
    "F1-Score": f1_score(y_test, y_pred_rf),
    "ROC-AUC": roc_auc_score(y_test, y_pred_rf)
}

rf_metrics_df = pd.DataFrame(rf_metrics, index=["RandomForest"])

rf_metrics_df

# Criar o modelo XGBoost com os melhores hiperparâmetros encontrados
xgb_best_model = XGBClassifier(
    colsample_bytree=0.8,
    learning_rate=0.1,
    max_depth=3,
    n_estimators=100,
    subsample=0.8,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)

# Treinar o modelo XGBoost nos dados balanceados
xgb_best_model.fit(X_resampled, y_resampled)

# Fazer previsões no conjunto de teste
y_pred_xgb = xgb_best_model.predict(X_test)

# Calcular métricas de avaliação para XGBoost
xgb_metrics = {
    "Acurácia": accuracy_score(y_test, y_pred_xgb),
    "Precisão": precision_score(y_test, y_pred_xgb),
    "Recall": recall_score(y_test, y_pred_xgb),
    "F1-Score": f1_score(y_test, y_pred_xgb),
    "ROC-AUC": roc_auc_score(y_test, y_pred_xgb)
}

# Criar um dataframe com os resultados
xgb_metrics_df = pd.DataFrame(xgb_metrics, index=["XGBoost"])

xgb_metrics_df

"""Como as métricas apresentaram valores muito bons, isso pode indicar overfitting. Vamos aplicar a validação cruzada para garantir que os modelos não estão enviezados.

Agora que temos os modelos criados e treinados com as melhores configurações de hyperparametros possíveis, vamos realizar a validação cruzada mais uma vez (pois ela foi realizada no gridsearch para encontrarmos os melhores valores) pois agora a realizaremos no modelo final já treinado com os hyperparametros.
"""

# Definir número de folds para a validação cruzada
cv_folds = 5

# Aplicar validação cruzada para Random Forest
rf_cv_scores = cross_val_score(rf_best_model, X_resampled, y_resampled, cv=cv_folds, scoring="accuracy", n_jobs=-1)
rf_cv_mean = rf_cv_scores.mean()

# Aplicar validação cruzada para XGBoost
xgb_cv_scores = cross_val_score(xgb_best_model, X_resampled, y_resampled, cv=cv_folds, scoring="accuracy", n_jobs=-1)
xgb_cv_mean = xgb_cv_scores.mean()

# Criar um dataframe com os resultados da validação cruzada
cv_results_df = pd.DataFrame({
    "Modelo": ["Random Forest", "XGBoost"],
    "Média Acurácia (Cross-Validation)": [rf_cv_mean, xgb_cv_mean]
})

cv_results_df

# Criar um dataframe com os resultados das métricas no conjunto de teste
final_results_df = pd.DataFrame({
    "Modelo": ["Random Forest", "XGBoost"],
    "Acurácia": [rf_metrics["Acurácia"], xgb_metrics["Acurácia"]],
    "Precisão": [rf_metrics["Precisão"], xgb_metrics["Precisão"]],
    "Recall": [rf_metrics["Recall"], xgb_metrics["Recall"]],
    "F1-Score": [rf_metrics["F1-Score"], xgb_metrics["F1-Score"]],
    "ROC-AUC": [rf_metrics["ROC-AUC"], xgb_metrics["ROC-AUC"]]
})

final_results_df

#Como os modelos são muito similares em performance, seguiremos com o random forest por ser um modelo de mais fácil interpretação.

import pickle

def salvar_modelo(modelo, nome_arquivo):
    """
    Salva o modelo treinado em um arquivo usando pickle.
    
    Parâmetros:
    modelo (objeto): Modelo treinado (Random Forest, XGBoost, etc.).
    nome_arquivo (str): Nome do arquivo para salvar o modelo.
    """
    with open(nome_arquivo, 'wb') as arquivo:
        pickle.dump(modelo, arquivo)
    print(f"Modelo salvo com sucesso em {nome_arquivo}")

# Exemplo de uso:
salvar_modelo(rf_best_model, "random_forest_model.pkl")
# salvar_modelo(xgb_best_model, "xgboost_model.pkl")

"""
As colunas que a base de dados nova precisa possuir para que o modelo consiga realizar a previsão corretamente são:

1.   QT_Parcelas_Atraso
2.   QT_Total_Parcelas_Pagas
3.   QT_Dias_Atraso
4.   VL_Parcela
5.   Valor_Renda
"""

