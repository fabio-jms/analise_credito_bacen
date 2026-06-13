import os
import matplotlib.pyplot as plt
import pandas as pd
from adjustText import adjust_text
from statsmodels.tsa.seasonal import seasonal_decompose  # Nova biblioteca estatística!

# 1. Configurações de caminhos para as séries de Concessão
pasta_dados = "dados_brutos"
arquivo_tt = os.path.join(pasta_dados, "Concessão_20631_CON_TOTAL.csv")
arquivo_pf = os.path.join(pasta_dados, "Concessão_20633_CON_PF_TOTAL.csv")
arquivo_pj = os.path.join(pasta_dados, "Concessão_20632_CON_PJ_TOTAL.csv")

# Verificar se os arquivos existem
arquivos_necessarios = [arquivo_tt, arquivo_pf, arquivo_pj]
for arq in arquivos_necessarios:
    if not os.path.exists(arq):
        print(f"Erro: O arquivo {arq} não foi encontrado. Altere os nomes no topo do script se necessário!")
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

# 3. FUNÇÃO MÁGICA DE DESSAZONALIZAÇÃO
def aplicar_dessazonalizacao(caminho_serie):
    df = ler_e_tratar(caminho_serie)
    
    # Para fazer a decomposição estatística, precisamos definir a coluna 'data' como o índice da tabela
    df.set_index("data", inplace=True)
    
    # Executa a decomposição. Como os dados do BACEN são mensais, o período (period) é 12 (um ano completo)
    # Usamos o modelo multiplicativo porque as variações sazonais tendem a crescer proporcionalmente ao volume
    decomposicao = seasonal_decompose(df["valor"], model="multiplicative", period=12)
    
    # Extraímos a Tendência (que é a série limpa do efeito gangorra dos meses)
    df["valor_dessazonalizado"] = decomposicao.trend
    
    # Como a média móvel centralizada da decomposição perde os primeiros 6 e os últimos 6 meses da série,
    # nós usamos o ajuste ajustado eliminando apenas o componente sazonal direto para manter os dados até a ponta final
    df["valor_dessazonalizado"] = df["valor"] / decomposicao.seasonal
    
    df.reset_index(inplace=True)
    # Filtrar a partir de 2020 para manter o padrão visual nítido
    return df[df["data"] >= "2020-01-01"].reset_index(drop=True)

# Processar as 3 séries de concessão
df_tt = aplicar_dessazonalizacao(arquivo_tt)
df_pf = aplicar_dessazonalizacao(arquivo_pf)
df_pj = aplicar_dessazonalizacao(arquivo_pj)

# 4. FUNÇÃO AUXILIAR DE RÓTULOS (R$ Milhões -> R$ Bilhões/Trilhões)
def formatar_label(valor_milhoes):
    valor_reais = valor_milhoes * 1_000_000
    if valor_reais >= 1_000_000_000_000:
        return f"R$ {valor_reais / 1_000_000_000_000:.2f} Tri"
    else:
        return f"R$ {valor_reais / 1_000_000_000:.0f} Bi"

# ==============================================================================
# CONSTRUÇÃO DO GRÁFICO DE CONCESSÕES DESSAZONALIZADAS
# ==============================================================================
fig, ax = plt.subplots(figsize=(14, 8))

cor_tt = "#2ca02c" 
cor_pf = "#1f77b4" 
cor_pj = "#ff7f0e" 
textos_labels = []

# --- PLOTAGEM DAS LINHAS ---
# Linha Contínua = Dados sem efeito sazonal (Tendência real do mercado)
# Linha Pontilhada = O fluxo bruto histórico com todos os saltos de dezembro/fevereiro
# TOTAL
ax.plot(df_tt["data"], df_tt["valor_dessazonalizado"], label="Concessão Total (Dessazonalizada)", color=cor_tt, linewidth=2.5)
ax.plot(df_tt["data"], df_tt["valor"], color=cor_tt, linestyle=":", linewidth=1.5, alpha=0.4)

# PESSOA FÍSICA
ax.plot(df_pf["data"], df_pf["valor_dessazonalizado"], label="Pessoa Física - PF (Dessazonalizada)", color=cor_pf, linewidth=2.5)
ax.plot(df_pf["data"], df_pf["valor"], color=cor_pf, linestyle=":", linewidth=1.5, alpha=0.4)

# PESSOA JURÍDICA
ax.plot(df_pj["data"], df_pj["valor_dessazonalizado"], label="Pessoa Jurídica - PJ (Dessazonalizada)", color=cor_pj, linewidth=2.5)
ax.plot(df_pj["data"], df_pj["valor"], color=cor_pj, linestyle=":", linewidth=1.5, alpha=0.4)

# --- INJETAR RÓTULOS AUTOMÁTICOS NAS EXTREMIDADES ---
for df_serie, cor in [(df_tt, cor_tt), (df_pf, cor_pf), (df_pj, cor_pj)]:
    # Ponto Inicial (Jan/2020)
    t_ini = ax.text(df_serie["data"].iloc[0], df_serie["valor_dessazonalizado"].iloc[0], 
                    formatar_label(df_serie["valor_dessazonalizado"].iloc[0]), color=cor, weight='bold', fontsize=9)
    # Ponto Final (Atual)
    t_fim = ax.text(df_serie["data"].iloc[-1], df_serie["valor_dessazonalizado"].iloc[-1], 
                    formatar_label(df_serie["valor_dessazonalizado"].iloc[-1]), color=cor, weight='bold', fontsize=9)
    textos_labels.extend([t_ini, t_fim])

# Organizar rótulos para não se cruzarem
adjust_text(textos_labels, ax=ax, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))

# Estética Final
ultimo_mes = df_tt["data"].iloc[-1].strftime("%m/%Y")
ax.set_title(f"Fluxo de Concessão de Crédito no Brasil (Visão Dessazonalizada vs Original até {ultimo_mes})", fontsize=14, fontweight="bold")
ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("Volume de Concessões Mensais", fontsize=12)
ax.grid(True, linestyle="--", alpha=0.5)
ax.legend(fontsize=10, loc="upper left", bbox_to_anchor=(1, 1))

plt.tight_layout()
print("Exibindo gráfico de concessões limpo de efeitos sazonais...")
plt.show()