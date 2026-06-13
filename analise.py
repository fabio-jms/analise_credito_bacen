import os
import matplotlib.pyplot as plt
import pandas as pd

# 1. Configurações de caminhos conforme as suas séries
pasta_dados = "dados_brutos"
arquivo_tt = os.path.join(pasta_dados, "Saldo_20539_SALDO_TOTAL.csv")
arquivo_pf = os.path.join(pasta_dados, "Saldo_20541_SALDO_PF_TOTAL.csv")
arquivo_pj = os.path.join(pasta_dados, "Saldo_20540_SALDO_PJ_TOTAL.csv")
arquivo_ipca = os.path.join(pasta_dados, "Indices_433_IPCA_MENSAL.csv")

# Verificar se todos os arquivos necessários existem
arquivos_necessarios = [arquivo_tt, arquivo_pf, arquivo_pj, arquivo_ipca]
for arq in arquivos_necessarios:
    if not os.path.exists(arq):
        print(f"Erro: O arquivo {arq} não foi encontrado. Verifique se o main.py já o baixou!")
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

# 3. Carregar e estruturar o IPCA (Deflator)
df_ipca = ler_e_tratar(arquivo_ipca)
df_ipca = df_ipca.rename(columns={"valor": "ipca_mes_pct"})
df_ipca["fator_mes"] = 1 + (df_ipca["ipca_mes_pct"] / 100)

# Acumular a inflação de trás para frente (trazendo para valor de hoje)
df_ipca = df_ipca.sort_values(by="data", ascending=False).reset_index(drop=True)
df_ipca["fator_acumulado"] = df_ipca["fator_mes"].cumprod()
df_ipca["fator_acumulado"] = df_ipca["fator_acumulado"] / df_ipca["fator_mes"]
df_ipca = df_ipca.sort_values(by="data").reset_index(drop=True)

# 4. Função auxiliar para cruzar dados e deflacionar cada série
def preparar_serie_deflacionada(caminho_serie):
    df_serie = ler_e_tratar(caminho_serie)
    # Cruzamento com a inflação
    df_fused = pd.merge(df_serie, df_ipca[["data", "fator_acumulado"]], on="data", how="inner")
    # Multiplica o nominal pelo fator para obter o valor real
    df_fused["valor_deflacionado"] = df_fused["valor"] * df_fused["fator_acumulado"]
    # Filtrar pós-2020 para o gráfico não ficar poluído
    return df_fused[df_fused["data"] >= "2020-01-01"]

# Processar as 3 séries de crédito
df_tt = preparar_serie_deflacionada(arquivo_tt)
df_pf = preparar_serie_deflacionada(arquivo_pf)
df_pj = preparar_serie_deflacionada(arquivo_pj)

# 5. CONSTRUÇÃO DO GRÁFICO MULTISSÉRIES
plt.figure(figsize=(14, 7))

# Configuração de Cores Uniformes
cor_tt = "#2ca02c" # Verde
cor_pf = "#1f77b4" # Azul
cor_pj = "#ff7f0e" # Laranja

# --- SÉRIE TOTAL ---
plt.plot(df_tt["data"], df_tt["valor_deflacionado"], label="Total (Real / Deflacionado)", color=cor_tt, linewidth=2.5)
plt.plot(df_tt["data"], df_tt["valor"], label="Total (Nominal)", color=cor_tt, linestyle=":", linewidth=2, alpha=0.7)

# --- SÉRIE PESSOA FÍSICA (PF) ---
plt.plot(df_pf["data"], df_pf["valor_deflacionado"], label="PF (Real / Deflacionado)", color=cor_pf, linewidth=2.5)
plt.plot(df_pf["data"], df_pf["valor"], label="PF (Nominal)", color=cor_pf, linestyle=":", linewidth=2, alpha=0.7)

# --- SÉRIE PESSOA JURÍDICA (PJ) ---
plt.plot(df_pj["data"], df_pj["valor_deflacionado"], label="PJ (Real / Deflacionado)", color=cor_pj, linewidth=2.5)
plt.plot(df_pj["data"], df_pj["valor"], label="PJ (Nominal)", color=cor_pj, linestyle=":", linewidth=2, alpha=0.7)

# Configurações Estéticas do Gráfico
ultimo_mes = df_tt["data"].iloc[-1].strftime("%m/%Y")
plt.title(f"Análise de Crédito no Brasil: Valores Nominais vs Reais (Base: {ultimo_mes})", fontsize=14, fontweight="bold")
plt.xlabel("Ano", fontsize=12)
plt.ylabel("Saldo em Milhões de Reais (R$)", fontsize=12)

plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(fontsize=10, loc="upper left", bbox_to_anchor=(1, 1)) # Move a legenda para fora se ficar muito grande
plt.tight_layout()

print("Gerando o gráfico completo comparativo...")
plt.show()