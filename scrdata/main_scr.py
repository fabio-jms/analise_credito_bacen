import os
import datetime
import requests

# 1. Configurações de caminhos
pasta_destino_scr = "dados_scr_brutos"
if not os.path.exists(pasta_destino_scr):
    os.makedirs(pasta_destino_scr)

# 2. Definir o intervalo de anos para testar
# A Versão 2 (v2) do SCR começou a rodar a partir de 2025. 
# Vamos configurar o script para varrer desde 2018 até o ano atual automaticamente.
ano_atual = datetime.datetime.now().year
anos_para_testar = list(range(2018, ano_atual + 1))

print(f"Iniciando varredura e download automatizado do SCR (Versão 2)...")
print(f"Anos mapeados para checagem: {anos_para_testar}\n")

# 3. Executar os downloads em lote
for ano in anos_para_testar:
    # Monta a URL exata conforme o padrão do servidor do BACEN
    url_download = f"https://www.bcb.gov.br/pda/desig/scrdata_{ano}.zip"
    nome_arquivo_zip = f"scrdata_{ano}.zip"
    caminho_salvamento = os.path.join(pasta_destino_scr, nome_arquivo_zip)
    
    print(f"Verificando disponibilidade para o ano {ano}...")
    
    try:
        # Fazemos uma requisição leve usando stream=True para checar o status antes de baixar
        with requests.get(url_download, stream=True, timeout=15) as r:
            # Se o status for 200, significa que o arquivo existe e está pronto para download
            if r.status_code == 200:
                print(f" -> Arquivo encontrado! Iniciando o download de {nome_arquivo_zip}...")
                
                # Baixa em blocos de memória para proteger o computador (chunks)
                with open(caminho_salvamento, "wb") as f:
                    for chunk in r.iter_content(chunk_size=16384): # Aumentado para 16kb para acelerar arquivos pesados
                        if chunk:
                            f.write(chunk)
                
                print(f" -> SUCESSO! Salvo em: {caminho_salvamento}")
            
            # Se der 404, o arquivo daquele ano específico ainda não foi gerado ou não existe nessa versão
            elif r.status_code == 404:
                print(f" -> Ignorado: Ano {ano} não está disponível no servidor (Status 404).")
            else:
                print(f" -> Alerta: Resposta inesperada para o ano {ano} (Status {r.status_code}).")
                
    except Exception as e:
        print(f" -> Falha ao tentar baixar o ano {ano}: {e}")

print("\n==================================================")
print("PROCESSO DE CAPTURA DO SCR CONCLUÍDO!")
print("==================================================")