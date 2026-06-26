import os
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# ==============================================================================
# 1. LOCALIZAR O ARQUIVO DO SCR (ABRIL DE 2026)
# ==============================================================================
pasta_scr_brutos = "dados_brutos_scrdata"

arquivo_zip_2026 = None
if os.path.exists(pasta_scr_brutos):
    zips_2026 = [f for f in os.listdir(pasta_scr_brutos) if "2026" in f and f.endswith(".zip")]
    if zips_2026:
        arquivo_zip_2026 = os.path.join(pasta_scr_brutos, sorted(zips_2026)[-1])

if not arquivo_zip_2026:
    print("Erro: ZIP de 2026 não encontrado.")
    exit()

# ==============================================================================
# 2. PROCESSAMENTO EM BLOCOS (CHUNKS) DE ABRIL/2026
# ==============================================================================
print("Iniciando extração e consolidação financeira de Abril/2026...")
blocos_agrupados = []

with zipfile.ZipFile(arquivo_zip_2026, "r") as z:
    lista_arquivos = z.namelist()
    # Procurando o mês de abril (202604)
    arquivos_abril = [f for f in lista_arquivos if "202604" in f and f.endswith(".csv")]
    
    if not arquivos_abril:
        print("Erro: CSV de Abril (202604) não encontrado dentro do ZIP.")
        exit()
        
    with z.open(arquivos_abril[0]) as f:
        contador = 0
        for chunk in pd.read_csv(f, sep=";", chunksize=200000, encoding="utf-8", low_memory=False):
            contador += 1
            if contador % 5 == 0:
                print(f" -> Processando bloco {contador}...")

            chunk.columns = [col.lower().strip() for col in chunk.columns]
            
            # Garantir colunas necessárias
            if not all(c in chunk.columns for c in ['submodalidade', 'segmento', 'carteira_ativa', 'carteira_inadimplencia']):
                continue
            
            # Limpeza textual das colunas de agrupamento
            chunk['submodalidade'] = chunk['submodalidade'].astype(str).str.strip()
            chunk['segmento'] = chunk['segmento'].astype(str).str.strip()
            
            # Limpeza e conversão financeira (Blindada)
            for col_valor in ['carteira_ativa', 'carteira_inadimplencia']:
                if not pd.api.types.is_numeric_dtype(chunk[col_valor]):
                    chunk[col_valor] = chunk[col_valor].astype(str).str.strip().str.replace('"', '', regex=False)
                    chunk[col_valor] = chunk[col_valor].str.replace(".", "", regex=False)
                    chunk[col_valor] = chunk[col_valor].str.replace(",", ".", regex=False)
                chunk[col_valor] = pd.to_numeric(chunk[col_valor], errors='coerce').fillna(0)
            
            # Agrupa os valores do bloco atual e guarda na lista
            df_agrupado_bloco = chunk.groupby(['submodalidade', 'segmento'])[['carteira_ativa', 'carteira_inadimplencia']].sum().reset_index()
            blocos_agrupados.append(df_agrupado_bloco)

# ==============================================================================
# 3. CONSOLIDAÇÃO MATEMÁTICA E REGRAS DE NEGÓCIO
# ==============================================================================
print("\nConsolidando indicadores finais...")
df_total = pd.concat(blocos_agrupados).groupby(['submodalidade', 'segmento']).sum().reset_index()

# A) Descobrir as Top 5 Submodalidades por Volume de Carteira Ativa Global
df_top5_nomes = df_total.groupby('submodalidade')['carteira_ativa'].sum().nlargest(5).index.tolist()

# B) Filtrar o dataframe para manter apenas os dados dessas 5 gigantes
df_top5 = df_total[df_total['submodalidade'].isin(df_top5_nomes)].copy()

# C) Calcular a Inadimplência da linha
df_top5['inadimplencia_pct'] = (df_top5['carteira_inadimplencia'] / df_top5['carteira_ativa']).fillna(0) * 100

# D) Preparar dados para o Gráfico 1 (Participação 100% por Segmento)
pivot_saldo = df_top5.pivot_table(index='submodalidade', columns='segmento', values='carteira_ativa', aggfunc='sum').fillna(0)
# Transforma os valores absolutos em porcentagem (soma da linha = 100%)
pivot_saldo_pct = pivot_saldo.div(pivot_saldo.sum(axis=1), axis=0) * 100

# E) Preparar dados para o Gráfico 2 (Inadimplência por Segmento)
pivot_inad = df_top5.pivot_table(index='submodalidade', columns='segmento', values='inadimplencia_pct', aggfunc='mean').fillna(0)

# ==============================================================================
# 4. CRIAÇÃO DO DASHBOARD GRÁFICO (Matplotlib)
# ==============================================================================
print("Gerando painel gráfico executivo...")

# Quebrar nomes longos das submodalidades para caberem bonitos no gráfico
labels_formatados = [textwrap.fill(nome, width=35) for nome in pivot_saldo_pct.index]

# Cria uma janela com 1 linha e 2 colunas (2 gráficos lado a lado)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9), gridspec_kw={'width_ratios': [1.2, 1]})

# --- GRÁFICO 1: Composição do Saldo (Barras Empilhadas 100%) ---
# O pandas tem um método direto para plotar barras empilhadas horizontais
pivot_saldo_pct.plot(kind='barh', stacked=True, ax=ax1, colormap='Set2', edgecolor='black', linewidth=0.5)

ax1.set_title("1. Market Share por Segmento (Composição da Carteira Ativa)", fontsize=14, weight='bold')
ax1.set_xlabel("Participação (%)")
ax1.set_ylabel("")
ax1.set_yticklabels(labels_formatados, fontsize=10)
ax1.set_xlim(0, 100)
ax1.legend(title='Segmento Instituição', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)

# Escrever a porcentagem no meio de cada pedaço da barra
for p in ax1.patches:
    width, height = p.get_width(), p.get_height()
    x, y = p.get_xy() 
    if width > 3: # Só escreve se o pedaço for maior que 3% para não embolar texto
        ax1.text(x + width/2, y + height/2, f'{width:.1f}%', ha='center', va='center', fontsize=8, weight='bold', color='white')

# --- GRÁFICO 2: Inadimplência por Segmento (Barras Agrupadas) ---
pivot_inad.plot(kind='barh', ax=ax2, colormap='Set2', edgecolor='black', linewidth=0.5)

ax2.set_title("2. Taxa de Inadimplência por Segmento (%)", fontsize=14, weight='bold')
ax2.set_xlabel("Inadimplência (%)")
ax2.set_ylabel("")
ax2.set_yticklabels([]) # Removemos os nomes do eixo Y aqui pois já estão no gráfico da esquerda
ax2.legend().remove() # Remove a legenda daqui pois o Gráfico 1 já tem

# Escrever o valor no topo de cada barra
for p in ax2.patches:
    width = p.get_width()
    if width > 0:
        ax2.text(width + 0.5, p.get_y() + p.get_height()/2, f'{width:.1f}%', va='center', fontsize=8)

# Ajuste estético da tela
plt.suptitle("Dashboard SCR (Abril/2026): Top 5 Produtos de Crédito vs Segmentação", fontsize=18, weight='bold', y=0.98)
plt.tight_layout()

# Salva a imagem em alta resolução
plt.savefig("dashboard_top5_abr2026.png", dpi=300, bbox_inches='tight')
print("Exibindo Painel...")
plt.show()