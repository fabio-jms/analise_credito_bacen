import os
import matplotlib.pyplot as plt
import pandas as pd

# 1. Configurações de caminhos
pasta_dados = "dados_brutos"
arquivo_tt = os.path.join(pasta_dados, "Saldo_20539_SALDO_TOTAL.csv")
arquivo_pf = os.path.join(pasta_dados, "Saldo_20541_SALDO_PF_TOTAL.csv")
arquivo_pj = os.path.join(pasta_dados, "Saldo_20540_SALDO_PJ_TOTAL.csv")
arquivo_ipca = os.path.join(pasta_dados, "Indices_433_IPCA_MENSAL.csv")

# Verificar se os arquivos existem
arquivos_necessarios = [arquivo_tt, arquivo_pf, arquivo_pj, arquivo_ipca]
for arq in arquivos_necessarios:
    if not os.path.exists(arq):
        print(f"Erro: O arquivo {arq} não foi encontrado.")
        exit()

# 2. Função para ler e tratar os dados
def ler_e_tratar(caminho):
    df = pd.read_csv(caminho, sep=";")
    if df["valor"].dtype == "object":
        df["valor"] = df["valor"].str.replace(",", ".").astype(float)
    else:
        df["valor"] = df["valor"].astype(float)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    return df.sort_values(by="data").reset_index(drop=True)

# 3. Carregar e estruturar o IPCA com BASE FIXA EM JANEIRO/2020
df_ipca = ler_e_tratar(arquivo_ipca)

# Filtrar o IPCA a partir de janeiro de 2020 (início do nosso gráfico)
df_ipca = df_ipca[df_ipca["data"] >= "2020-01-01"].sort_values(by="data").reset_index(drop=True)
df_ipca = df_ipca.rename(columns={"valor": "ipca_mes_pct"})

# Calcular o fator mensal
df_ipca["fator_mes"] = 1 + (df_ipca["ipca_mes_pct"] / 100)

# A MÁGICA: Acumular a inflação para FRENTE cronologicamente
# O primeiro mês (Jan/2020) começará sem inflação acumulada para trás dele
df_ipca["fator_acumulado"] = df_ipca["fator_mes"].cumprod()
# Ajustar para que o primeiro mês da série seja exatamente 1.0 (dividir pelo fator do primeiro mês)
df_ipca["fator_acumulado"] = df_ipca["fator_acumulado"] / df_ipca["fator_mes"].iloc[0]

# 4. Função para cruzar e deflacionar com base no início
def preparar_serie_base_inicio(caminho_serie):
    df_serie = ler_e_tratar(caminho_serie)
    # Filtrar a série de crédito também a partir de Jan/2020
    df_serie = df_serie[df_serie["data"] >= "2020-01-01"]
    
    df_fused = pd.merge(df_serie, df_ipca[["data", "fator_acumulado"]], on="data", how="inner")
    
    # Para trazer o valor para o poder de compra do INÍCIO (Jan/2020),
    # nós DIVIDIMOS o valor nominal pelo fator acumulado da inflação daquele mês
    df_fused["valor_deflacionado"] = df_fused["valor"] / df_fused["fator_acumulado"]
    return df_fused

# Processar as séries
df_tt = preparar_serie_base_inicio(arquivo_tt)
df_pf = preparar_serie_base_inicio(arquivo_pf)
df_pj = preparar_serie_base_inicio(arquivo_pj)

# 5. CONSTRUÇÃO DO GRÁFICO
plt.figure(figsize=(14, 7))

# Cores
cor_tt = "#2ca02c" # Verde
cor_pf = "#1f77b4" # Azul
cor_pj = "#ff7f0e" # Laranja

# Plotar as linhas (Repare que em 2020-01-01 os valores nominal e deflacionado serão idênticos)
# --- TOTAL ---
plt.plot(df_tt["data"], df_tt["valor_deflacionado"], label="Total (Real - Poder de compra de Jan/20)", color=cor_tt, linewidth=2.5)
plt.plot(df_tt["data"], df_tt["valor"], label="Total (Nominal)", color=cor_tt, linestyle=":", linewidth=2, alpha=0.7)

# --- PESSOA FÍSICA ---
plt.plot(df_pf["data"], df_pf["valor_deflacionado"], label="PF (Real - Poder de compra de Jan/20)", color=cor_pf, linewidth=2.5)
plt.plot(df_pf["data"], df_pf["valor"], label="PF (Nominal)", color=cor_pf, linestyle=":", linewidth=2, alpha=0.7)

# --- PESSOA JURÍDICA ---
plt.plot(df_pj["data"], df_pj["valor_deflacionado"], label="PJ (Real - Poder de compra de Jan/20)", color=cor_pj, linewidth=2.5)
plt.plot(df_pj["data"], df_pj["valor"], label="PJ (Nominal)", color=cor_pj, linestyle=":", linewidth=2, alpha=0.7)

# Estética
plt.title("Evolução do Crédito no Brasil: Valores Nominais vs Reais (Base Fixa: Janeiro/2020)", fontsize=14, fontweight="bold")
plt.xlabel("Ano", fontsize=12)
plt.ylabel("Saldo em Milhões de Reais (R$)", fontsize=12)

plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=10, loc="upper left", bbox_to_anchor=(1, 1))
plt.tight_layout()

print("Gerando o gráfico com ponto de partida comum...")
plt.show()