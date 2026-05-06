import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

import matplotlib.pyplot as plt

CAMINHO_CREDENCIAIS = r"C:\temp\projeto-TCC\credenciais.json"
ID_PLANILHA = "1oQgFTTb6MEdZLMJkz-Lb-93MY2DpsYz5M_Lx-Tfqi28"
NOME_ABA = "Creches"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    CAMINHO_CREDENCIAIS,
    scope
)

cliente = gspread.authorize(creds)
worksheet = cliente.open_by_key(ID_PLANILHA).worksheet(NOME_ABA)
dados = worksheet.get("B2:K32")
cabecalho = dados[0]
linhas = dados[1:]

df = pd.DataFrame(
    linhas,
    columns=cabecalho
)

df.columns = df.columns.str.strip()

def limpar_moeda(valor):
    valor = str(valor)
    valor = valor.replace("R$", "")
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")
    valor = valor.strip()

    return float(valor)

# orçamento
df["Orçamento"] = df["Orçamento"].apply(limpar_moeda)

# porcentagens
colunas_percentuais = [
    "% Execução Física",
    "% Execução Financeira",
    "Diferença Fisico Financeiro",
    "Pazo Consumido",
    "Indice Atraso"
]

for coluna in colunas_percentuais:
    df[coluna] = (
        df[coluna]
        .astype(str)
        .str.replace(",", ".")
        .astype(float)
    )

features = [
    "Orçamento",
    "% Execução Física",
    "% Execução Financeira",
    "Diferença Fisico Financeiro",
    "Pazo Consumido",
    "Indice Atraso"
]

X = df[features]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

modelo = IsolationForest(
    contamination=0.10,
    random_state=42
)

df["Anomalia"] = modelo.fit_predict(X_scaled)
df.loc[
    df["Diferença Fisico Financeiro"] < 0,
    "Anomalia"
] = -1

anomalias = df[df["Anomalia"] == -1]
cores = df["Anomalia"].map({
    1: "blue",
    -1: "red"
})
plt.figure(figsize=(14, 8))

plt.scatter(
    df["% Execução Física"],
    df["Indice Atraso"],
    c=cores,
    s=120
)
plt.xlabel("% Execução Física")
plt.ylabel("Índice de Atraso")
plt.title(
    "Detecção de Anomalias em Obras da CEHAB"
)

for i, row in anomalias.iterrows():

    plt.text(
        row["% Execução Física"],
        row["Indice Atraso"],
        row["Obra"],
        fontsize=8
    )

print("\n=== OBRAS ANÔMALAS DETECTADAS ===\n")

for i, row in anomalias.iterrows():

    problemas = []

    if row["% Execução Física"] < 30:
        problemas.append(
            "baixa execução física"
        )

    if (
        row["% Execução Financeira"]
        >
        row["% Execução Física"]
    ):
        problemas.append(
            "execução financeira maior que física"
        )

    if row["Indice Atraso"] > 50:
        problemas.append(
            "alto índice de atraso"
        )

    if row["Pazo Consumido"] > 90:
        problemas.append(
            "prazo contratual quase esgotado"
        )

    if row["Orçamento"] > 5000000:
        problemas.append(
            "orçamento elevado"
        )

    print(f"{row['Obra']}:\n")

    for p in problemas:
        print(f" - {p}")

    print()

plt.grid(True)

plt.show()
