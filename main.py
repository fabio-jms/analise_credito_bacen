import os
import time
import pandas as pd
import requests

# 1. Criar um dicionário com as séries de crédito que queremos baixar
# O formato é: "Nome_do_Arquivo": Código_no_BACEN
series_credito = {
    "credito_total": 20539,
    "credito_pessoa_fisica": 20540,
    "credito_pessoa_juridica": 20541,
    # Você pode adicionar novas séries aqui futuramente seguindo o mesmo padrão!
}

# 2. Garantir que a pasta de destino existe
pasta_destino = "dados_brutos"
if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)
    print(f"Pasta '{pasta_destino}' criada!")

print("Iniciando o download do lote de séries temporais...\n")

# 3. Criar um laço 'for' para repetir o processo para cada item do dicionário
for nome_serie, codigo in series_credito.items():
    print(f"Buscando {nome_serie} (Série {codigo})...")
    
    # Construir a URL para a série atual
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
    
    try:
        resposta = requests.get(url)
        
        if resposta.status_code == 200:
            dados_json = resposta.json()
            df = pd.DataFrame(dados_json)
            
            # Definir o caminho do arquivo usando o nome descritivo que demos
            caminho_arquivo = os.path.join(pasta_destino, f"{nome_serie}.csv")
            
            # Salvar em CSV separado por ponto e vírgula
            df.to_csv(caminho_arquivo, index=False, sep=";")
            print(f"-> Sucesso! Salvo em: {caminho_arquivo} ({len(df)} registros encontrados)")
        else:
            print(f"-> Erro ao acessar a série {codigo}. Status: {resposta.status_code}")
            
    except Exception as e:
        print(f"-> Ocorreu uma falha na requisição: {e}")
    
    # 4. Uma boa prática: esperar 1 segundo entre as requisições para não sobrecarregar o servidor deles
    time.sleep(1)

print("\n--- Todos os downloads foram concluídos! ---")