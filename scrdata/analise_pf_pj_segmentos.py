import os
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

# ==============================================================================
# 1. LOCALIZAR ARQUIVO E LER EM BLOCOS
# ==============================================================================
pasta_scr_brutos = "dados_brutos_scrdata"
arquivo_zip = [f for f in os.listdir(pasta_scr_brutos) if "2026" in f and f.endswith(".zip")]

if not arquivo_zip:
    print("Erro: ZIP de 2026 não encontrado.")
    exit()

arquivo_zip_path = os.path.join(pasta_scr_brutos, sorted(arquivo_zip)[-1])
blocos_agrupados = []

print("Lendo volumes financeiros e segmentando por Tipo de Cliente (PF/PJ)...")
with zipfile.ZipFile(arquivo_zip_path, "r") as z:
    csv_alvo = [f for f in z.namelist() if "202604" in f and f.endswith(".csv")][0]
    
    with z.open(csv_alvo) as f:
        for chunk in pd.read_csv(f, sep=";", chunksize=200000, encoding="utf-8", low_memory=False):
            chunk.columns = [col.lower().strip() for col in chunk.columns]
            
            # Garantir que a coluna 'cliente' exista no arquivo
            if not all(col in chunk.columns for col in ['submodalidade', 'segmento', 'cliente']):
                continue
            
            chunk['submodalidade'] = chunk['submodalidade'].astype(str).str.strip()
            chunk['segmento'] = chunk['segmento'].astype(str).str.strip()
            # Tratamento da coluna Cliente (PF e PJ)
            chunk['cliente'] = chunk['cliente'].astype(str).str.strip().str.upper() 
            
            if not pd.api.types.is_numeric_dtype(chunk['carteira_ativa']):
                chunk['carteira_ativa'] = chunk['carteira_ativa'].astype(str).str.replace('"', '').str.replace(".", "").str.replace(",", ".").str.strip()
            
            chunk['carteira_ativa'] = pd.to_numeric(chunk['carteira_ativa'], errors='coerce').fillna(0)
            
            # Agrupa adicionando o nível de Cliente
            df_bloco = chunk.groupby(['segmento', 'cliente', 'submodalidade'])['carteira_ativa'].sum().reset_index()
            blocos_agrupados.append(df_bloco)

# ==============================================================================
# 2. FILTRAGEM, CONSOLIDAÇÃO E RANKEAMENTO DUPLO
# ==============================================================================
print("Calculando o Market Share interno separado por Varejo e Atacado...")
df_total = pd.concat(blocos_agrupados).groupby(['segmento', 'cliente', 'submodalidade']).sum().reset_index()

# Padronizações de limpeza
df_total['segmento_limpo'] = df_total['segmento'].str.lower()

# A) Filtragem e Agrupamento de Segmentos (Regra de Negócio)
segmentos_remover = ['outros', 'arrendamento', 'desenvolvimento']
df_total = df_total[~df_total['segmento_limpo'].isin(segmentos_remover)].copy()
df_total = df_total[df_total['cliente'].isin(['PF', 'PJ'])].copy() # Garante apenas PF e PJ limpos

mapeamento_canais = {
    'fintech': 'Fintech + IP', 'ip': 'Fintech + IP',
    'banco': 'Banco', 'cooperativa': 'Cooperativa', 'financeira': 'Financeira'
}
df_total['segmento_consolidado'] = df_total['segmento_limpo'].map(mapeamento_canais).fillna(df_total['segmento'])

df_consolidado = df_total.groupby(['segmento_consolidado', 'cliente', 'submodalidade'])['carteira_ativa'].sum().reset_index()

# B) Ranking em Janela (Top 5 por Segmento E por Tipo de Cliente)
tamanho_subcarteira = df_consolidado.groupby(['segmento_consolidado', 'cliente'])['carteira_ativa'].transform('sum')
df_consolidado['peso_pct'] = (df_consolidado['carteira_ativa'] / tamanho_subcarteira) * 100

df_rank = df_consolidado.sort_values(['segmento_consolidado', 'cliente', 'carteira_ativa'], ascending=[True, True, False])
top5_final = df_rank.groupby(['segmento_consolidado', 'cliente']).head(5).copy()

# ==============================================================================
# 3. CONSTRUÇÃO DA MATRIZ GRÁFICA (GRID 4x2)
# ==============================================================================
print("Gerando painel visual de raio-x (Varejo vs Atacado)...")

segmentos_finais = ['Banco', 'Cooperativa', 'Financeira', 'Fintech + IP']
tipos_cliente = ['PF', 'PJ']
cores_cliente = {'PF': '#1f77b4', 'PJ': '#ff7f0e'} # PF será Azul, PJ será Laranja

fig, axes = plt.subplots(nrows=len(segmentos_finais), ncols=len(tipos_cliente), figsize=(22, 18))

for i, segmento in enumerate(segmentos_finais):
    for j, cliente in enumerate(tipos_cliente):
        ax = axes[i, j]
        
        df_plot = top5_final[(top5_final['segmento_consolidado'] == segmento) & (top5_final['cliente'] == cliente)].sort_values('peso_pct', ascending=True)
        
        # Caso algum segmento não tenha PF ou PJ cadastrado, pula a plotagem gracefully
        if df_plot.empty:
            ax.axis('off')
            continue
            
        labels = [textwrap.fill(nome, width=45) for nome in df_plot['submodalidade']]
        cor = cores_cliente[cliente]
        
        barras = ax.barh(labels, df_plot['peso_pct'], color=cor, edgecolor='black', alpha=0.85)
        
        ax.set_title(f"{segmento.upper()} - {cliente}", fontsize=13, weight='bold')
        ax.set_xlim(0, 100)
        
        # Ajustes visuais para não poluir o eixo X
        if i == len(segmentos_finais) - 1:
            ax.set_xlabel("Peso na Subcarteira (%)", fontsize=11)
        else:
            ax.set_xticklabels([])
            
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        for barra in barras:
            width = barra.get_width()
            if width > 0.1:
                ax.text(width + 1.5, barra.get_y() + barra.get_height()/2, f'{width:.1f}%', 
                        va='center', fontsize=10, weight='bold')

plt.suptitle("DNA de Crédito Duplo: Varejo (PF) vs Atacado (PJ) por Segmento (Abr/26)", fontsize=22, weight='bold', y=0.97)
plt.tight_layout(pad=2.0, rect=[0, 0, 1, 0.95])

plt.savefig("dna_produtos_pf_pj.png", dpi=300, bbox_inches='tight')
print("Exibindo matriz gráfica...")
plt.show()