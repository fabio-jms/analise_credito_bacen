import os
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

# 1. Configurações de caminhos
arquivo_dados = "resultado_inadimplencia_scr_2025.csv"
arquivo_mapa_local = "br_states.json"

# Validação de segurança dos arquivos locais
if not os.path.exists(arquivo_dados):
    print(f"Erro: O arquivo '{arquivo_dados}' não foi encontrado. Rode o analise_scr_cartoes.py primeiro!")
    exit()

if not os.path.exists(arquivo_mapa_local):
    print(f"Erro: O arquivo geofráfico '{arquivo_mapa_local}' não foi encontrado na pasta do projeto!")
    exit()

print("Carregando resultados da inadimplência do SCR...")
df_inad = pd.read_csv(arquivo_dados, sep=";")

# 2. Filtrar o período mais recente para a foto do mapa (Dezembro de 2025)
data_recente = "2025-12-31"
df_recente = df_inad[df_inad['data_base'] == data_recente].copy()

# Fallback defensivo caso a string da data no seu CSV use outro padrão
if df_recente.empty:
    data_recente = df_inad['data_base'].max()
    df_recente = df_inad[df_inad['data_base'] == data_recente].copy()

print(f"Gerando mapas analíticos para a data-base: {data_recente}")

# Separar os dados em dois blocos (Bancos e Fintechs)
df_bancos = df_recente[df_recente['segmento'] == 'Banco'].copy()
df_fintechs = df_recente[df_recente['segmento'] == 'Fintech'].copy()

# ==============================================================================
# 3. CARREGAR E PADRONIZAR A MALHA GEOGRÁFICA LOCAL
# ==============================================================================
print("Carregando as fronteiras do Brasil a partir do arquivo local...")
mapa_brasil = gpd.read_file(arquivo_mapa_local)

# Adaptar a propriedade 'id' do novo arquivo JSON para virar a nossa coluna 'uf'
if 'id' in mapa_brasil.columns:
    mapa_brasil = mapa_brasil.rename(columns={'id': 'uf'})

# Garantir padronização rigorosa de texto: letras maiúsculas e sem espaços ocultos
mapa_brasil['uf'] = mapa_brasil['uf'].astype(str).str.strip().str.upper()
df_bancos['uf'] = df_bancos['uf'].astype(str).str.strip().str.upper()
df_fintechs['uf'] = df_fintechs['uf'].astype(str).str.strip().str.upper()

# 4. UNIR OS DADOS FINANCEIROS AO MAPA (Merge Geográfico)
mapa_bancos = mapa_brasil.merge(df_bancos, on='uf', how='left')
mapa_fintechs = mapa_brasil.merge(df_fintechs, on='uf', how='left')

# Preencher estados sem correspondência ou sem dados com 0
mapa_bancos['inadimplencia_pct'] = mapa_bancos['inadimplencia_pct'].fillna(0)
mapa_fintechs['inadimplencia_pct'] = mapa_fintechs['inadimplencia_pct'].fillna(0)

# Descobrir o maior valor de inadimplência global para fixar a mesma escala de cor nos dois mapas
max_inad = max(mapa_bancos['inadimplencia_pct'].max(), mapa_fintechs['inadimplencia_pct'].max())

# ==============================================================================
# 5. CONFIGURAÇÃO E PLOTAGEM DOS MAPAS LADO A LADO
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Paleta de cores: vai do Amarelo (baixo risco) ao Vermelho Escuro (alto risco)
paleta_cores = "YlOrRd"

# ------------------------------------------------------------------------------
# MAPA 1: BANCOS TRADICIONAIS
# ------------------------------------------------------------------------------
mapa_bancos.plot(
    column='inadimplencia_pct',
    cmap=paleta_cores,
    linewidth=0.8,
    ax=ax1,
    edgecolor='gray',
    vmin=0,
    vmax=max_inad
)
ax1.set_title("Inadimplência em Cartão de Crédito: BANCOS", fontsize=14, fontweight="bold", color="#1f77b4")
ax1.axis('off')  # Remove os eixos de latitude/longitude para limpar o visual

# Adicionar os rótulos de texto (Sigla + %) no centroide de cada estado
for idx, row in mapa_bancos.iterrows():
    if row['geometry'] and row['inadimplencia_pct'] > 0:
        centroide = row['geometry'].centroid
        ax1.text(
            centroide.x, centroide.y, 
            f"{row['uf']}\n{row['inadimplencia_pct']:.1f}%", 
            fontsize=8, ha='center', va='center', weight='bold', color='black'
        )

# ------------------------------------------------------------------------------
# MAPA 2: FINTECHS
# ------------------------------------------------------------------------------
mapa_fintechs.plot(
    column='inadimplencia_pct',
    cmap=paleta_cores,
    linewidth=0.8,
    ax=ax2,
    edgecolor='gray',
    vmin=0,
    vmax=max_inad
)
ax2.set_title("Inadimplência em Cartão de Crédito: FINTECHS", fontsize=14, fontweight="bold", color="#ff7f0e")
ax2.axis('off')

for idx, row in mapa_fintechs.iterrows():
    if row['geometry'] and row['inadimplencia_pct'] > 0:
        centroide = row['geometry'].centroid
        ax2.text(
            centroide.x, centroide.y, 
            f"{row['uf']}\n{row['inadimplencia_pct']:.1f}%", 
            fontsize=8, ha='center', va='center', weight='bold', color='black'
        )

# ------------------------------------------------------------------------------
# BARRA DE CORES GLOBAL (Legenda unificada à direita)
# ------------------------------------------------------------------------------
scalar_mappable = plt.cm.ScalarMappable(cmap=paleta_cores, norm=plt.Normalize(vmin=0, vmax=max_inad))
cbar = fig.colorbar(scalar_mappable, ax=[ax1, ax2], orientation='vertical', fraction=0.02, pad=0.04)
cbar.set_label("Taxa de Inadimplência (%)", fontsize=12, weight='bold')

plt.suptitle(f"Análise de Risco Regional no Mercado de Cartões (SCR data-base: {data_recente})", fontsize=16, fontweight="bold", y=0.95)

# Salvar a imagem final em alta definição (300 DPI)
plt.savefig("mapa_comparativo_inadimplencia.png", dpi=300, bbox_inches='tight')

print("Exibindo mapa de calor geográfico...")
plt.show()