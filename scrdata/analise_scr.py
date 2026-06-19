import os
import zipfile
import pandas as pd

# 1. Configurações de caminhos
pasta_dados_scr = "dados_scr_brutos"
# Altere para o ano que você conseguiu baixar com sucesso no passo anterior
nome_arquivo_zip = "scrdata_2018.zip" 
caminho_zip = os.path.join(pasta_dados_scr, nome_arquivo_zip)

# Verificar se o arquivo zip realmente existe
if not os.path.exists(caminho_zip):
    print(f"Erro: O arquivo {caminho_zip} não foi encontrado. Rode o main_scr.py primeiro!")
    exit()

print(f"Abrindo o arquivo {nome_arquivo_zip} sem descompactar no Windows...")

# 2. Utilizar o zipfile para inspecionar o conteúdo do pacote
with zipfile.ZipFile(caminho_zip, 'r') as z:
    # Captura a lista de todos os arquivos que estão dentro do arquivo .zip
    lista_arquivos_internos = z.namelist()
    print(f"Arquivos encontrados dentro do ZIP: {lista_arquivos_internos}")
    
    # Filtramos para pegar o primeiro arquivo que termine com .csv ou .txt
    arquivo_csv_interno = [f for f in lista_arquivos_internos if f.endswith('.csv') or f.endswith('.txt')][0]
    print(f"Identificado arquivo de dados: '{arquivo_csv_interno}'")
    
    # 3. A MÁGICA: Abrir o arquivo de dentro do zip e passar direto para o Pandas
    # O comando z.open() abre o arquivo diretamente em fluxo de memória (stream)
    with z.open(arquivo_csv_interno) as f:
        print("\nCarregando as primeiras 5 linhas para inspeção estrutural...")
        
        # Como os arquivos do SCR são gigantescos, NUNCA dê um read_csv puro sem o 'nrows' no início, 
        # sob o risco de travar o seu computador por falta de memória RAM!
        df_amostra = pd.read_csv(
            f, 
            sep=";", 
            nrows=5, 
            encoding="utf-8" # Ajuste o encoding se os caracteres vierem quebrados (ex: latin1 ou iso-8859-1)
        )

# 4. Exibir a estrutura na tela
print("\n==================================================")
print("             AMOSTRA DE DADOS DO SCR              ")
print("==================================================")
print(f"Colunas identificadas ({len(df_amostra.columns)}):")
print(list(df_amostra.columns))
print("\nVisualização das primeiras linhas:")
print(df_amostra)
print("==================================================")