import os
import pandas as pd

# 1. Configuração dos caminhos locais
# Dica: Mova o seu arquivo baixado para uma pasta de brutos dentro de ifdata
arquivo_entrada = "ifdata_pf_202603.csv"

if not os.path.exists(arquivo_entrada):
    # Procura defensiva caso o script mude de diretório de execução
    arquivo_entrada = os.path.join("ifdata\dados_ifdata_brutos", arquivo_entrada)

if not os.path.exists(arquivo_entrada):
    print(f"Erro: O arquivo '{arquivo_entrada}' não foi localizado. Coloque-o na raiz ou na pasta ifdata/.")
    exit()

print("1. Extraindo a estrutura de cabeçalho de dupla camada...")

# Ler estritamente as duas primeiras linhas para achatar a matriz de colunas
df_headers = pd.read_csv(arquivo_entrada, sep=";", nrows=2, header=None, encoding="utf-8") 

# Linha 0: Macro-modalidades. O .ffill() arrasta o nome (ex: 'Veículos') para a direita 
# preenchendo os campos que eram nulos devido à mesclagem de células do Excel/Portal.
linha_0_preenchida = df_headers.iloc[0].ffill()

# Linha 1: Prazos e Status da carteira
linha_1 = df_headers.iloc[1]

# Combinar as duas linhas de forma cirúrgica
novos_cabecalhos = []
for c0, c1 in zip(linha_0_preenchida, linha_1):
    c0_limpo = str(c0).strip()
    
    # Se a linha 1 for nula ou vazia, significa que estamos nas colunas de cadastro (Instituição, Código, UF...)
    if pd.isna(c1) or str(c1).strip() == "":
        novos_cabecalhos.append(c0_limpo)
    else:
        c1_limpo = str(c1).strip()
        # Mescla os dois níveis com um sublinhado para criar uma coluna plana e legível
        novos_cabecalhos.append(f"{c0_limpo}_{c1_limpo}")

print("2. Carregando os dados financeiros e removendo notas de rodapé...")

# Ler o arquivo pulando as 2 linhas de cabeçalho originais
df_dados = pd.read_csv(arquivo_entrada, sep=";", skiprows=2, header=None, encoding="utf-8")
df_dados.columns = novos_cabecalhos

# ==============================================================================
# NOVO: FILTRO DE RODAPÉ (LIXO NO FIM DO ARQUIVO) - BLINDADO
# ==============================================================================
# Em vez de usar o nome com acento, capturamos o nome real que o Pandas deu
# para a coluna 0 (Instituição) e coluna 1 (Código) após a leitura.
col_instituicao = df_dados.columns[0]
col_codigo = df_dados.columns[1]

# Removemos qualquer linha onde a coluna Código esteja vazia (NaN)
df_dados = df_dados.dropna(subset=[col_codigo]).copy()

# Para garantir, removemos também linhas onde a Instituição seja apenas um traço ou vazio
df_dados = df_dados[df_dados[col_instituicao].astype(str).str.strip() != '']

# ==============================================================================
# 3. DATA CLEANING: TRATAMENTO DOS PADRÕES NUMÉRICOS BRASILEIROS
# ==============================================================================
print("3. Convertendo strings financeiras (pontos, vírgulas e %) para Float...")

colunas_cadastro = ['Instituição', 'Código', 'TCB', 'TD', 'TC', 'SR', 'Cidade', 'UF', 'Data']
colunas_financeiras = [col for col in df_dados.columns if col not in colunas_cadastro]

for col in colunas_financeiras:
    # Garante tipo string para aplicar as substituições textuais com segurança
    df_dados[col] = df_dados[col].astype(str).str.strip()
    
    # Remove símbolos de porcentagem se houver
    df_dados[col] = df_dados[col].str.replace('%', '', regex=False)
    
    # Remove o ponto divisor de milhar brasileiro (15.865.718 -> 15865718)
    df_dados[col] = df_dados[col].str.replace('.', '', regex=False)
    
    # Substitui a vírgula decimal por ponto padrão internacional do Python
    df_dados[col] = df_dados[col].str.replace(',', '.', regex=False)
    
    # Neutraliza hifens ou nulos gerados pelo sistema do BACEN convertendo para zero
    df_dados[col] = df_dados[col].replace(['nan', '-', '', 'None'], '0')
    
    # Força a conversão para número puro (Float/Int)
    df_dados[col] = pd.to_numeric(df_dados[col], errors='coerce').fillna(0)

# 4. Exportar o dataframe final limpo e estruturado para modelagem ou gráficos
pasta_saida = "ifdata" if os.path.exists("ifdata") else "."
arquivo_saida = os.path.join(pasta_saida, "ifdata_pf_carteira_limpa.csv")

df_dados.to_csv(arquivo_saida, sep=";", index=False, encoding="utf-8-sig") 
print(f"\n[SUCESSO] Base do IFData processada com {df_dados.shape[0]} linhas e {df_dados.shape[1]} colunas.")
print(f"-> Arquivo pronto salvo em: {arquivo_saida}")