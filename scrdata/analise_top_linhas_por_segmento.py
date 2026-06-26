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
            
            # Limpeza rápida e agrupamento do bloco
            chunk['submodalidade'] = chunk['submodalidade'].astype(str).str.strip()
            chunk['segmento'] = chunk['segmento'].astype(str).str.strip()
            
            if not pd.api.types.is_numeric_dtype(chunk['carteira_ativa']):
                chunk['carteira_ativa'] = chunk['carteira_ativa'].astype(str).str.replace('"', '').str.replace(".", "").str.replace(",", ".").str.strip()
            
            chunk['carteira_ativa'] = pd.to_numeric(chunk['carteira_ativa'], errors='coerce').fillna(0)
            
            df_bloco = chunk.groupby(['segmento', 'submodalidade'])['carteira_ativa'].sum().reset_index()
            blocos_agrupados.append(df_bloco)

# ==============================================================================
# 2. ENGENHARIA DE RANKING (O Segredo da Análise)
# ==============================================================================
print("Calculando o peso das carteiras e ranqueando os carros-chefes...")
df_total = pd.concat(blocos_agrupados).groupby(['segmento', 'submodalidade']).sum().reset_index()

# 2.1 Descobrir o tamanho total da carteira de CADA segmento
tamanho_segmento = df_total.groupby('segmento')['carteira_ativa'].transform('sum')

# 2.2 Calcular a representatividade (%) da linha dentro daquele segmento específico
df_total['peso_no_segmento_pct'] = (df_total['carteira_ativa'] / tamanho_segmento) * 100

# 2.3 Rankear: Ordena por Segmento e Volume (do maior pro menor), e corta os 5 primeiros de cada!
df_rank = df_total.sort_values(['segmento', 'carteira_ativa'], ascending=[True, False])
top5_por_segmento = df_rank.groupby('segmento').head(5).copy()

# ==============================================================================
# 3. CONSTRUÇÃO DA MATRIZ GRÁFICA (GRID 2x2)
# ==============================================================================
print("Gerando painel visual...")

# Para o gráfico não ficar gigante, vamos pegar os 4 maiores segmentos do Brasil
top_4_segmentos = df_total.groupby('segmento')['carteira_ativa'].sum().nlargest(4).index.tolist()

# Prepara a tela de pintura: 2 linhas, 2 colunas
fig, axes = plt.subplots(2, 2, figsize=(18, 12))
axes = axes.flatten() # Transforma a matriz 2x2 em uma lista simples para o loop

cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # Cores diferentes para cada segmento

for i, segmento in enumerate(top_4_segmentos):
    ax = axes[i]
    
    # Filtra os dados apenas daquele segmento e inverte a ordem para a maior barra ficar no topo do gráfico
    df_plot = top5_por_segmento[top5_por_segmento['segmento'] == segmento].sort_values('peso_no_segmento_pct', ascending=True)
    
    # Quebra de texto inteligente para nomes longos de submodalidades
    labels = [textwrap.fill(nome, width=40) for nome in df_plot['submodalidade']]
    
    # Plota as barras horizontais
    barras = ax.barh(labels, df_plot['peso_no_segmento_pct'], color=cores[i], edgecolor='black', alpha=0.8)
    
    ax.set_title(f"Carros-Chefes: {segmento.upper()}", fontsize=14, weight='bold')
    ax.set_xlim(0, 100) # Fixa o eixo X em 100% para os 4 gráficos terem a mesma proporção visual
    ax.set_xlabel("Peso na Carteira do Segmento (%)", fontsize=10)
    
    # Escreve a porcentagem na ponta de cada barra
    for barra in barras:
        width = barra.get_width()
        ax.text(width + 1.5, barra.get_y() + barra.get_height()/2, f'{width:.1f}%', 
                va='center', fontsize=10, weight='bold', color='black')

plt.suptitle("DNA de Crédito: Principais Produtos por Segmento de Instituição (Abr/26)", fontsize=18, weight='bold', y=0.96)
plt.tight_layout(pad=3.0)

plt.savefig("dna_produtos_por_segmento.png", dpi=300, bbox_inches='tight')
print("Exibindo matriz gráfica...")
plt.show()