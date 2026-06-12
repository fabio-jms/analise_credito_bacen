import pandas as pd
import requests

# 1. Definir o código da série do BACEN (20539 = Crédito total do sistema financeiro)
codigo_serie = 20539

# 2. Construir a URL da API oficial do Banco Central
url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?formato=json"

print("Buscando dados no Banco Central... Por favor, aguarde.")

# 3. Fazer a requisição para o site do BACEN
resposta = requests.get(url)

# 4. Verificar se a conexão deu certo (Código 200 significa OK)
if resposta.status_code == 200:
    # Transformar os dados recebidos (JSON) em uma tabela do Pandas (DataFrame)
    dados_json = resposta.json()
    df = pd.DataFrame(dados_json)
    
    # Exibir as 10 últimas linhas da tabela para ver o progresso recente
    print("\n--- Dados de Crédito Carregados com Sucesso! ---")
    print(df.tail(10))
else:
    print(f"Erro ao acessar a API. Código do erro: {resposta.status_code}")