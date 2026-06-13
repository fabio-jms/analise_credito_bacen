import os
import matplotlib.pyplot as plt
import pandas as pd

# 1. Definir o caminho dos arquivos que baixamos
pasta_dados = "dados_brutos"
arquivo_tt = os.path.join(pasta_dados, "Concessão_20631_CON_TOTAL.csv")
arquivo_pf = os.path.join(pasta_dados, "Concessão_20633_CON_PF_TOTAL.csv")
arquivo_pj = os.path.join(pasta_dados, "Concessão_20632_CON_PJ_TOTAL.csv")

# 2. Ler os arquivos CSV usando o Pandas
# Lembra que salvamos usando o separador ponto e vírgula (sep=";")? Precisamos avisar o Pandas aqui.
df_tt = pd.read_csv(arquivo_tt, sep=";")
df_pf = pd.read_csv(arquivo_pf, sep=";")
df_pj = pd.read_csv(arquivo_pj, sep=";")


# 3. TRATAMENTO DOS DADOS (Essencial!)
# O Banco Central nos envia os números com vírgula (ex: 1250,50) e o Python não entende isso como número, mas como texto.
# Além disso, precisamos converter a coluna de data para o formato que o Python entende.
def tratar_dados(df):
    # 1. Verificar se a coluna 'valor' veio como texto (object/string)
    if df["valor"].dtype == "object":
        # Se for texto, fazemos a substituição da vírgula por ponto
        df["valor"] = df["valor"].str.replace(",", ".").astype(float)
    else:
        # Se já for número (int ou float), apenas garantimos que seja float
        df["valor"] = df["valor"].astype(float)

    # 2. Transforma o texto da data em um objeto de data real do Python
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")

    # 3. Filtrar para pegar apenas os dados de 2020 em diante
    df = df[df["data"] >= "2020-01-01"]

    return df


# Aplicar o tratamento nas duas tabelas
df_tt = tratar_dados(df_tt)
df_pf = tratar_dados(df_pf)
df_pj = tratar_dados(df_pj)


# 4. CRIANDO O GRÁFICO
# Definimos o tamanho da imagem (largura, altura)
plt.figure(figsize=(12, 6))

# Plotar a linha de Total (Eixo X = data, Eixo Y = valor)
plt.plot(
    df_tt["data"],
    df_tt["valor"],
    label="Crédito Total",
    color="blue",
    linewidth=2,
)

# Plotar a linha de Pessoa Física
plt.plot(
    df_pf["data"],
    df_pf["valor"],
    label="Crédito Pessoa Física (PF)",
    color="green",
    linewidth=2,
)

# Plotar a linha de Pessoa Jurídica
plt.plot(
    df_pj["data"],
    df_pj["valor"],
    label="Crédito Pessoa Jurídica (PJ)",
    color="orange",
    linewidth=2,
)

# Configurações estéticas do gráfico (Títulos e Legendas)
plt.title("Evolução do Saldo de Operações de Crédito no Brasil (Pós-2020)", fontsize=14, fontweight="bold")
plt.xlabel("Ano", fontsize=12)
plt.ylabel("Saldo em Milhões de Reais (R$)", fontsize=12)

# Adiciona linhas de grade ao fundo para facilitar a leitura
plt.grid(True, linestyle="--", alpha=0.6)

# Mostra a legenda que criamos nos 'label' lá em cima
plt.legend(fontsize=11)

# Ajusta o layout para não cortar nada
plt.tight_layout()

# Exibir o gráfico na tela!
print("Gerando o gráfico... Uma nova janela deve se abrir.")
plt.show()