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

print("Lendo microdados e isolando Pessoas Físicas (PF)...")
with zipfile.ZipFile(arquivo_zip_path, "r") as z:
    csv_alvo = [f for f in z.namelist() if "202604" in f and f.endswith(".csv")][0]
    
    with z.open(csv_alvo) as f:
        contador = 0
        for chunk in pd.read_csv(f, sep=";", chunksize=200000, encoding="utf-8", low_memory=False):
            contador += 1
            if contador % 5 == 0:
                print(f" -> Processando bloco {contador}...")

            chunk.columns = [col.lower().strip() for col in chunk.columns]
            
            # Garantir que as colunas necessárias existam
            colunas_necessarias = ['cliente', 'cnae_ocupacao', 'porte', 'carteira_ativa', 'modalidade']
            if not all(col in chunk.columns for col in colunas_necessarias):
                continue
            
            # 1. FILTRO CIRÚRGICO DUPLO: Apenas PF e Financiamento Imobiliário
            chunk['cliente'] = chunk['cliente'].astype(str).str.strip().str.upper()
            chunk['modalidade'] = chunk['modalidade'].astype(str).str.strip()

            # Criamos as duas condições isoladas
            condicao_pf = chunk['cliente'] == 'PF'
            condicao_imob = chunk['modalidade'] == 'Financiamentos imobiliários'

            # Juntamos as duas com o operador & (E)
            chunk_pf = chunk[condicao_pf & condicao_imob].copy()
            
            if chunk_pf.empty:
                continue
            
            # Limpeza de texto
            chunk_pf['cnae_ocupacao'] = chunk_pf['cnae_ocupacao'].astype(str).str.strip()
            chunk_pf['porte'] = chunk_pf['porte'].astype(str).str.strip()
            
            # Conversão financeira da carteira
            if not pd.api.types.is_numeric_dtype(chunk_pf['carteira_ativa']):
                chunk_pf['carteira_ativa'] = chunk_pf['carteira_ativa'].astype(str).str.replace('"', '').str.replace(".", "").str.replace(",", ".")
            
            chunk_pf['carteira_ativa'] = pd.to_numeric(chunk_pf['carteira_ativa'], errors='coerce').fillna(0)
            
            # Agrupamento do bloco
            df_bloco = chunk_pf.groupby(['cnae_ocupacao', 'porte'])['carteira_ativa'].sum().reset_index()
            blocos_agrupados.append(df_bloco)

# ==============================================================================
# 2. CONSOLIDAÇÃO MATEMÁTICA E TOP 10 OCUPAÇÕES
# ==============================================================================
print("Consolidando volumes e ranqueando as Ocupações...")
df_total = pd.concat(blocos_agrupados).groupby(['cnae_ocupacao', 'porte'])['carteira_ativa'].sum().reset_index()

# O BACEN costuma colocar códigos ou 'Não informado'. Vamos remover valores inválidos óbvios se houver
df_total = df_total[df_total['cnae_ocupacao'] != 'nan']

# Descobrir as Top 10 Ocupações com MAIOR volume de crédito total
top10_ocupacoes = df_total.groupby('cnae_ocupacao')['carteira_ativa'].sum().nlargest(10).index.tolist()

# Filtrar o DataFrame apenas para as top 10
df_top10 = df_total[df_total['cnae_ocupacao'].isin(top10_ocupacoes)].copy()

# Criar a Tabela Dinâmica (Pivot) para o Gráfico de Barras Empilhadas
# Linhas = Ocupações, Colunas = Porte (Faixa de Renda), Valores = Dinheiro
pivot_ocupacao = df_top10.pivot_table(index='cnae_ocupacao', columns='porte', values='carteira_ativa', aggfunc='sum').fillna(0)

# Ordenar o Pivot Table para que a ocupação com maior total fique no topo do gráfico
pivot_ocupacao['Total'] = pivot_ocupacao.sum(axis=1)
pivot_ocupacao = pivot_ocupacao.sort_values('Total', ascending=True).drop(columns=['Total'])

# ==============================================================================
# NOVO: ORDENAÇÃO LÓGICA DAS FAIXAS DE RENDA (PORTE)
# ==============================================================================
# Esta é a escadinha padrão do BACEN. Ajuste os nomes se no seu JSON estiverem diferentes.
ordem_renda_oficial = [
    'Sem rendimento',
    'Até 1 salário mínimo',
    'Mais de 1 a 2 salários mínimos',
    'Mais de 2 a 3 salários mínimos',
    'Mais de 3 a 5 salários mínimos',
    'Mais de 5 a 10 salários mínimos',
    'Mais de 10 a 20 salários mínimos',
    'Mais de 20 salários mínimos',
    'Não informado',
    'Indisponível'
]

# 1. Pegamos da nossa lista apenas as categorias que realmente apareceram nos dados
colunas_ordenadas = [col for col in ordem_renda_oficial if col in pivot_ocupacao.columns]

# 2. Se houver alguma categoria nova no CSV que não prevemos, garantimos que ela vá para o final
colunas_extras = [col for col in pivot_ocupacao.columns if col not in ordem_renda_oficial]

# 3. Reorganizamos as colunas (que viram as cores empilhadas) na ordem perfeita
pivot_ocupacao = pivot_ocupacao[colunas_ordenadas + colunas_extras]

# ==============================================================================
# 3. VISUALIZAÇÃO GRÁFICA (Barras Empilhadas)
# ==============================================================================
print("Gerando painel gráfico executivo...")

# Quebra de texto para nomes de profissões muito longas
pivot_ocupacao.index = [textwrap.fill(nome, width=35) for nome in pivot_ocupacao.index]

# Plotagem
fig, ax = plt.subplots(figsize=(16, 10))

# Usa um mapa de cores (colormap) bacana para diferenciar as faixas de renda
pivot_ocupacao.plot(kind='barh', stacked=True, ax=ax, colormap='Spectral', edgecolor='black', linewidth=0.5)

ax.set_title("Top 10 Ocupações PF por Volume de Crédito e Faixa de Renda (Abr/26)", fontsize=18, weight='bold')
ax.set_xlabel("Volume de Carteira Ativa (R$ Bilhões)", fontsize=12)
ax.set_ylabel("")

# Formatar o eixo X para mostrar os números em Bilhões
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"R$ {x/1e9:,.0f} B".replace(',', '.')))

# Ajustar a legenda (Porte/Renda) para fora do gráfico
plt.legend(title="Porte do Cliente (Renda)", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10, title_fontsize=12)

plt.tight_layout()

# Salvar e mostrar
plt.savefig("perfil_renda_ocupacao_pf.png", dpi=300, bbox_inches='tight')
print("Exibindo mapa de perfil PF...")
plt.show()