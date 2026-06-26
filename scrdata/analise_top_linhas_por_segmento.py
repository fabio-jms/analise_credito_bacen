import os
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

# ==============================================================================
# 1. LOCALIZAR ARQUIVO E LER EM BLOCOS (Motor Base)
# ==============================================================================
pasta_scr_brutos = "dados_brutos_scrdata"
arquivo_zip = [f for f in os.listdir(pasta_scr_brutos) if "2026" in f and f.endswith(".zip")]

if not arquivo_zip:
    print("Erro: ZIP de 2026 não encontrado.")
    exit()

arquivo_zip_path = os.path.join(pasta_scr_brutos, sorted(arquivo_zip)[-1])
blocos_agrupados = []

print("Lendo volumes financeiros do SCR (Abril/2026)...")
with zipfile.ZipFile(arquivo_zip_path, "r") as z:
    csv_alvo = [f for f in z.namelist() if "202604" in f and f.endswith(".csv")][0]
    
    with z.open(csv_alvo) as f:
        for chunk in pd.read_csv(f, sep=";", chunksize=200000, encoding="utf-8", low_memory=False):
            chunk.columns = [col.lower().strip() for col in chunk.columns]
            
            if 'submodalidade' not in chunk.columns or 'segmento' not in chunk.columns:
                continue
            
            chunk['submodalidade'] = chunk['submodalidade'].astype(str).str.strip()
            chunk['segmento'] = chunk['segmento'].astype(str).str.strip()
            
            if not pd.api.types.is_numeric_dtype(chunk['carteira_ativa']):
                chunk['carteira_ativa'] = chunk['carteira_ativa'].astype(str).str.replace('"', '').str.replace(".", "").str.replace(",", ".").str.strip()
            
            chunk['carteira_ativa'] = pd.to_numeric(chunk['carteira_ativa'], errors='coerce').fillna(0)
            
            df_bloco = chunk.groupby(['segmento', 'submodalidade'])['carteira_ativa'].sum().reset_index()
            blocos_agrupados.append(df_bloco)

# ==============================================================================
# 2. FILTRAGEM, TRATAMENTO E REAGRUPAMENTO DOS SEGMENTOS
# ==============================================================================
print("Tratando regras de negócio e agrupando IP + Fintech...")
df_total = pd.concat(blocos_agrupados).groupby(['segmento', 'submodalidade']).sum().reset_index()

# Padronização de texto defensiva para a comparação
df_total['segmento_limpo'] = df_total['segmento'].str.lower().str.strip()

# A) Remover segmentos irrelevantes para esta análise
segmentos_remover = ['outros', 'arrendamento', 'desenvolvimento']
df_total = df_total[~df_total['segmento_limpo'].isin(segmentos_remover)].copy()

# B) Agrupar IP e Fintech sob a mesma nomenclatura
mapeamento_canais = {
    'fintech': 'Fintech + IP',
    'ip': 'Fintech + IP',
    'banco': 'Banco',
    'cooperativa': 'Cooperativa',
    'financeira': 'Financeira'
}
df_total['segmento_consolidado'] = df_total['segmento_limpo'].map(mapeamento_canais).fillna(df_total['segmento'])

# C) Como mudamos os grupos, re-agrupamos para somar os valores de Fintech e IP que agora são o mesmo grupo
df_consolidado = df_total.groupby(['segmento_consolidado', 'submodalidade'])['carteira_ativa'].sum().reset_index()

# ==============================================================================
# 3. ENGENHARIA DE RANKING (Apenas nos 4 segmentos finais)
# ==============================================================================
# Calcular o tamanho total da carteira de CADA um dos 4 novos grupos
tamanho_segmento = df_consolidado.groupby('segmento_consolidado')['carteira_ativa'].transform('sum')
df_consolidado['peso_no_segmento_pct'] = (df_consolidado['carteira_ativa'] / tamanho_segmento) * 100

# Rankear o top 5 de cada grupo
df_rank = df_consolidado.sort_values(['segmento_consolidado', 'carteira_ativa'], ascending=[True, False])
top5_por_segmento = df_rank.groupby('segmento_consolidado').head(5).copy()

# ==============================================================================
# 4. CONSTRUÇÃO DA MATRIZ GRÁFICA REFINADA (GRID 2x2)
# ==============================================================================
print("Gerando painel visual otimizado...")

# Lista ordenada dos 4 segmentos para plotagem
segmentos_finais = ['Banco', 'Cooperativa', 'Financeira', 'Fintech + IP']

fig, axes = plt.subplots(2, 2, figsize=(18, 12))
axes = axes.flatten()

# Paleta de cores cirúrgica para destacar o ecossistema digital
cores = ['#1f77b4', '#2ca02c', '#9467bd', '#ff7f0e'] 

for i, segmento in enumerate(segmentos_finais):
    ax = axes[i]
    
    # Filtra e ordena para manter o maior produto no topo do gráfico de barras horizontais
    df_plot = top5_por_segmento[top5_por_segmento['segmento_consolidado'] == segmento].sort_values('peso_no_segmento_pct', ascending=True)
    
    labels = [textwrap.fill(nome, width=40) for nome in df_plot['submodalidade']]
    
    barras = ax.barh(labels, df_plot['peso_no_segmento_pct'], color=cores[i], edgecolor='black', alpha=0.85)
    
    ax.set_title(f"Carros-Chefes: {segmento.upper()}", fontsize=14, weight='bold')
    ax.set_xlim(0, 100)
    ax.set_xlabel("Peso na Carteira do Segmento (%)", fontsize=10)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    for barra in barras:
        width = barra.get_width()
        if width > 0.1:
            ax.text(width + 1.5, barra.get_y() + barra.get_height()/2, f'{width:.1f}%', 
                    va='center', fontsize=10, weight='bold', color='black')

plt.suptitle("DNA de Crédito Refinado: Principais Produtos por Segmento Otimizado (Abr/26)", fontsize=18, weight='bold', y=0.96)
plt.tight_layout(pad=3.0, rect=[0, 0, 1, 0.95])

plt.savefig("dna_produtos_segmentos_refinado.png", dpi=300, bbox_inches='tight')
print("Exibindo matriz gráfica refinada...")
plt.show()