import os
import pandas as pd
import requests

# 1. Definir o código da série do BACEN (20539 = Crédito total do sistema financeiro)
codigo_serie = 20539

# 2. Criar uma pasta para os dados brutos (se ela já não existir)
pasta_destino = "dados_brutos"
if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)
    print(f"Pasta '{pasta_destino}' criada com sucesso!")

# 3. Construir a URL da API oficial do Banco Central
url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?formato=json"

print("Buscando dados no Banco Central... Por favor, aguarde.")
resposta = requests.get(url)

if resposta.status_code == 200:
    dados_json = resposta.json()
    df = pd.DataFrame(dados_json)
    
    # 4. Definir o nome do arquivo final (ex: dados_brutos/serie_20539.csv)
    caminho_arquivo = os.path.join(pasta_destino, f"serie_{codigo_serie}.csv")
    
    # 5. Salvar a tabela em formato CSV
    # index=False serve para o Pandas não criar uma coluna de numeração extra
    df.to_csv(caminho_arquivo, index=False, sep=";")
    
    print(f"\n--- Dados salvos com sucesso em: {caminho_arquivo} ---")
    print(df.tail(5))
else:
    print(f"Erro ao acessar a API. Código: {resposta.status_code}")