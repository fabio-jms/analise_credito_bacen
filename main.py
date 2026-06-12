import os
import time
import pandas as pd
import requests

# 1. Definir o nome do arquivo da sua planilha que está na pasta
arquivo_planilha = "codigos_series_bacen.csv"

# 2. Ler a planilha usando o Pandas
print(f"Lendo a planilha de séries: {arquivo_planilha}")
df_planilha = pd.read_csv(arquivo_planilha, sep=";")

# 3. Garantir que a pasta de destino para os downloads existe
pasta_destino = "dados_brutos"
if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)
    print(f"Pasta '{pasta_destino}' criada!")

print(f"Total de séries encontradas na planilha: {len(df_planilha)}")
print("Iniciando o download massivo...\n")

# 4. Percorrer cada linha da sua planilha automaticamente
for index, linha in df_planilha.iterrows():
    codigo = linha["CODIGO"]
    # Usamos o nome abreviado para salvar o arquivo de forma limpa
    nome_arquivo = linha["NOME_ABREV"]
    classe = linha["Classe"]
    
    print(f"[{index + 1}/{len(df_planilha)}] Baixando {classe} -> {nome_arquivo} (Série {codigo})...")
    
    # Construir a URL da API do BACEN
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
    
    try:
        resposta = requests.get(url)
        
        if resposta.status_code == 200:
            dados_json = resposta.json()
            df_serie = pd.DataFrame(dados_json)
            
            # O nome do arquivo vai conter a classe para organizar melhor (ex: dados_brutos/ICC_ICC_PF_TOTAL.csv)
            caminho_final = os.path.join(pasta_destino, f"{classe}_{nome_arquivo}.csv")
            
            # Salvar os dados brutos da série
            df_serie.to_csv(caminho_final if 'caminhi_final' not in locals() else os.path.join(pasta_destino, f"{classe}_{nome_arquivo}.csv"), index=False, sep=";")
            print(f"   -> Sucesso! {len(df_serie)} registros salvos.")
        else:
            print(f"   -> Erro ao acessar série {codigo}. Status: {resposta.status_code}")
            
    except Exception as e:
        print(f"   -> Falha na requisição da série {codigo}: {e}")
    
    # Pausa de 1 segundo para ser gentil com o servidor do BACEN
    time.sleep(1)

print("\n--- Download em lote de todas as séries concluído com sucesso! ---")