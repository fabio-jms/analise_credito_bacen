import os
import matplotlib.pyplot as plt
import pandas as pd
from adjustText import adjust_text

# 1. Configurações de caminhos
pasta_dados = "dados_brutos_sgs"
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

# Carregar dados básicos
df_raw_tt = ler_e_tratar(arquivo_tt)
df_raw_pf = ler_e_tratar(arquivo_pf)
df_raw_pj = ler_e_tratar(arquivo_pj)
df_raw_ipca = ler_e_tratar(arquivo_ipca)

data_inicio = "2020-01-01"

# ==============================================================================
# VISÃO 1: DEFLAÇÃO COM BASE NO PRESENTE
# ==============================================================================
df_ipca_pres = df_raw_ipca.copy()
df_ipca_pres["fator_mes"] = 1 + (df_ipca_pres["valor"] / 100)
df_ipca_pres = df_ipca_pres.sort_values(by="data", ascending=False).reset_index(drop=True)
df_ipca_pres["fator_acumulado"] = df_ipca_pres["fator_mes"].cumprod() / df_ipca_pres["fator_mes"]
df_ipca_pres = df_ipca_pres.sort_values(by="data").reset_index(drop=True)

def deflacionar_presente(df_credito):
    df_fused = pd.merge(df_credito, df_ipca_pres[["data", "fator_acumulado"]], on="data", how="inner")
    df_fused["valor_deflacionado"] = df_fused["valor"] * df_fused["fator_acumulado"]
    return df_fused[df_fused["data"] >= data_inicio].reset_index(drop=True)

df_tt_pres = deflacionar_presente(df_raw_tt)
df_pf_pres = deflacionar_presente(df_raw_pf)
df_pj_pres = deflacionar_presente(df_raw_pj)

# ==============================================================================
# VISÃO 2: DEFLAÇÃO COM BASE NO INÍCIO (Jan/2020)
# ==============================================================================
df_ipca_ini = df_raw_ipca[df_raw_ipca["data"] >= data_inicio].sort_values(by="data").reset_index(drop=True)
df_ipca_ini["fator_mes"] = 1 + (df_ipca_ini["valor"] / 100)
df_ipca_ini["fator_acumulado"] = df_ipca_ini["fator_mes"].cumprod() / df_ipca_ini["fator_mes"].iloc[0]

def deflacionar_inicio(df_credito):
    df_sub = df_credito[df_credito["data"] >= data_inicio]
    df_fused = pd.merge(df_sub, df_ipca_ini[["data", "fator_acumulado"]], on="data", how="inner")
    df_fused["valor_deflacionado"] = df_fused["valor"] / df_fused["fator_acumulado"]
    return df_fused.reset_index(drop=True)

df_tt_ini = deflacionar_inicio(df_raw_tt)
df_pf_ini = deflacionar_inicio(df_raw_pf)
df_pj_ini = deflacionar_inicio(df_raw_pj)


# ==============================================================================
# FUNÇÃO AUXILIAR PARA FORMATAR OS VALORES (R$ Milhões -> R$ Bilhões/Trilhões)
# ==============================================================================
def format_label(valor_milhoes):
    valor_reais = valor_milhoes * 1_000_000
    if valor_reais >= 1_000_000_000_000:
        return f"R$ {valor_reais / 1_000_000_000_000:.2f} Tri"
    else:
        return f"R$ {valor_reais / 1_000_000_000:.0f} Bi"


# ==============================================================================
# CONFIGURAÇÃO DA JANELA DOS GRÁFICOS
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11), sharex=True)

cor_tt = "#2ca02c" 
cor_pf = "#1f77b4" 
cor_pj = "#ff7f0e" 
ultimo_mes = df_tt_pres["data"].iloc[-1].strftime("%m/%Y")

# ------------------------------------------------------------------------------
# PLOT GRÁFICO 1: Visão Original (Rótulos apenas no INÍCIO para não poluir)
# ------------------------------------------------------------------------------
ax1.plot(df_tt_pres["data"], df_tt_pres["valor_deflacionado"], label="Total (Real - Preços de Hoje)", color=cor_tt, linewidth=2.5)
ax1.plot(df_tt_pres["data"], df_tt_pres["valor"], label="Total (Nominal)", color=cor_tt, linestyle=":", linewidth=2, alpha=0.7)

ax1.plot(df_pf_pres["data"], df_pf_pres["valor_deflacionado"], label="PF (Real - Preços de Hoje)", color=cor_pf, linewidth=2.5)
ax1.plot(df_pf_pres["data"], df_pf_pres["valor"], label="PF (Nominal)", color=cor_pf, linestyle=":", linewidth=2, alpha=0.7)

ax1.plot(df_pj_pres["data"], df_pj_pres["valor_deflacionado"], label="PJ (Real - Preços de Hoje)", color=cor_pj, linewidth=2.5)
ax1.plot(df_pj_pres["data"], df_pj_pres["valor"], label="PJ (Nominal)", color=cor_pj, linestyle=":", linewidth=2, alpha=0.7)

# Injetar rótulos de texto no ponto inicial (Índice 0) de cada linha do Gráfico 1
for df_serie, cor in [(df_tt_pres, cor_tt), (df_pf_pres, cor_pf), (df_pj_pres, cor_pj)]:
    # Valor Nominal Inicial
    ax1.annotate(format_label(df_serie["valor"].iloc[0]), 
                 xy=(df_serie["data"].iloc[0], df_serie["valor"].iloc[0]),
                 xytext=(-10, 5), textcoords='offset points', color=cor, weight='bold', fontsize=9, ha='right')
    # Valor Real Inicial
    ax1.annotate(format_label(df_serie["valor_deflacionado"].iloc[0]), 
                 xy=(df_serie["data"].iloc[0], df_serie["valor_deflacionado"].iloc[0]),
                 xytext=(-10, -12), textcoords='offset points', color=cor, weight='bold', fontsize=9, ha='right')

ax1.set_title(f"Visão 1: Valores Trazidos para o Presente (Base Referência: {ultimo_mes}) \n[Rótulos de valores aplicados apenas no início histórico]", fontsize=12, fontweight="bold")
ax1.set_ylabel("Saldo", fontsize=11)
ax1.grid(True, linestyle="--", alpha=0.5)
ax1.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1, 1))


# ==============================================================================
# CONFIGURAÇÃO DA JANELA DOS GRÁFICOS
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11), sharex=True)

cor_tt = "#2ca02c" 
cor_pf = "#1f77b4" 
cor_pj = "#ff7f0e" 
ultimo_mes = df_tt_pres["data"].iloc[-1].strftime("%m/%Y")

# Criamos listas vazias para guardar as referências dos textos de cada gráfico
textos_ax1 = []
textos_ax2 = []

# ------------------------------------------------------------------------------
# PLOT GRÁFICO 1: Visão Original (Rótulos apenas no INÍCIO)
# ------------------------------------------------------------------------------
ax1.plot(df_tt_pres["data"], df_tt_pres["valor_deflacionado"], label="Total (Real - Preços de Hoje)", color=cor_tt, linewidth=2.5)
ax1.plot(df_tt_pres["data"], df_tt_pres["valor"], label="Total (Nominal)", color=cor_tt, linestyle=":", linewidth=2, alpha=0.7)

ax1.plot(df_pf_pres["data"], df_pf_pres["valor_deflacionado"], label="PF (Real - Preços de Hoje)", color=cor_pf, linewidth=2.5)
ax1.plot(df_pf_pres["data"], df_pf_pres["valor"], label="PF (Nominal)", color=cor_pf, linestyle=":", linewidth=2, alpha=0.7)

ax1.plot(df_pj_pres["data"], df_pj_pres["valor_deflacionado"], label="PJ (Real - Preços de Hoje)", color=cor_pj, linewidth=2.5)
ax1.plot(df_pj_pres["data"], df_pj_pres["valor"], label="PJ (Nominal)", color=cor_pj, linestyle=":", linewidth=2, alpha=0.7)

# Injetar rótulos no ponto inicial (Índice 0)
for df_serie, cor in [(df_tt_pres, cor_tt), (df_pf_pres, cor_pf), (df_pj_pres, cor_pj)]:
    # Guardamos o texto criado dentro da lista usando t1 e t2
    t1 = ax1.text(df_serie["data"].iloc[0], df_serie["valor"].iloc[0], 
                 format_label(df_serie["valor"].iloc[0]), color=cor, weight='bold', fontsize=9)
    t2 = ax1.text(df_serie["data"].iloc[0], df_serie["valor_deflacionado"].iloc[0], 
                 format_label(df_serie["valor_deflacionado"].iloc[0]), color=cor, weight='bold', fontsize=9)
    textos_ax1.extend([t1, t2])

# A MÁGICA DO AX1: Alinha os textos de forma que nenhum se sobreponha
adjust_text(textos_ax1, ax=ax1, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))

ax1.set_title(f"Visão 1: Valores Trazidos para o Presente (Base Referência: {ultimo_mes})", fontsize=12, fontweight="bold")
ax1.set_ylabel("Saldo", fontsize=11)
ax1.grid(True, linestyle="--", alpha=0.5)
ax1.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1, 1))

# ------------------------------------------------------------------------------
# PLOT GRÁFICO 2: Visão Nova (Rótulos apenas no FINAL)
# ------------------------------------------------------------------------------
ax2.plot(df_tt_ini["data"], df_tt_ini["valor_deflacionado"], label="Total (Real - Poder de compra Jan/20)", color=cor_tt, linewidth=2.5)
ax2.plot(df_tt_ini["data"], df_tt_ini["valor"], label="Total (Nominal)", color=cor_tt, linestyle=":", linewidth=2, alpha=0.7)

ax2.plot(df_pf_ini["data"], df_pf_ini["valor_deflacionado"], label="PF (Real - Poder de compra Jan/20)", color=cor_pf, linewidth=2.5)
ax2.plot(df_pf_ini["data"], df_pf_ini["valor"], label="PF (Nominal)", color=cor_pf, linestyle=":", linewidth=2, alpha=0.7)

ax2.plot(df_pj_ini["data"], df_pj_ini["valor_deflacionado"], label="PJ (Real - Poder de compra Jan/20)", color=cor_pj, linewidth=2.5)
ax2.plot(df_pj_ini["data"], df_pj_ini["valor"], label="PJ (Nominal)", color=cor_pj, linestyle=":", linewidth=2, alpha=0.7)

# Injetar rótulos no ponto final (Índice -1)
for df_serie, cor in [(df_tt_ini, cor_tt), (df_pf_ini, cor_pf), (df_pj_ini, cor_pj)]:
    t1 = ax2.text(df_serie["data"].iloc[-1], df_serie["valor"].iloc[-1], 
                 format_label(df_serie["valor"].iloc[-1]), color=cor, weight='bold', fontsize=9)
    t2 = ax2.text(df_serie["data"].iloc[-1], df_serie["valor_deflacionado"].iloc[-1], 
                 format_label(df_serie["valor_deflacionado"].iloc[-1]), color=cor, weight='bold', fontsize=9)
    textos_ax2.extend([t1, t2])

# A MÁGICA DO AX2: Repete o ajuste inteligente para o segundo painel
adjust_text(textos_ax2, ax=ax2, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))

ax2.set_title("Visão 2: Valores Mantidos na Base do Passado (Base Referência: Janeiro/2020)", fontsize=12, fontweight="bold")
ax2.set_xlabel("Ano", fontsize=11)
ax2.set_ylabel("Saldo", fontsize=11)
ax2.grid(True, linestyle="--", alpha=0.5)
ax2.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1, 1))

# Ajustes Finais de Layout
plt.tight_layout()
print("Exibindo gráficos consolidados com repelente de sobreposição...")
plt.show()