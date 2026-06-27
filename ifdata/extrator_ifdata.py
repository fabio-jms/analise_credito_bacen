import os
import requests
import pandas as pd
import time

# ==============================================================================
# CONFIGURAÇÕES DA API OLINDA (BACEN)
# ==============================================================================
# Base URL do serviço IFData na API Olinda
BASE_URL = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata"



# Headers padronizados para evitar bloqueios
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ==============================================================================
# PASSO 1 E 2: MAPEAMENTO DE DOMÍNIOS (METADADOS)
# ==============================================================================
def obter_relatorios():
    """Busca o catálogo de códigos de relatórios disponíveis no IFData."""
    print("1. Baixando catálogo de Relatórios...")
    url = f"{BASE_URL}/ListaDeRelatorio()?$top=100&$format=json"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    dados = response.json()['value']
    df_relatorios = pd.DataFrame(dados)
    
    # Salva localmente para não precisar bater na API toda hora
    df_relatorios.to_csv("ifdata/dominio_relatorios.csv", index=False, sep=";")
    print(f" -> Sucesso! {len(df_relatorios)} relatórios mapeados.")
    return df_relatorios

def obter_instituicoes_financeiras():
    """Busca o cadastro de todas as IFs mapeadas pelo Banco Central."""
    print("2. Baixando catálogo de Instituições Financeiras (IFs)...")
    url = f"{BASE_URL}/IfDataCadastro(AnoMes=@AnoMes)?@AnoMes='202603'&$top=100&$format=json"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    dados = response.json()['value']
    df_ifs = pd.DataFrame(dados)
    
    df_ifs.to_csv("ifdata/dominio_ifs.csv", index=False, sep=";")
    print(f" -> Sucesso! {len(df_ifs)} instituições mapeadas.")
    return df_ifs

# ==============================================================================
# PASSO 3: EXTRAÇÃO DOS DADOS FINANCEIROS CRUZADOS
# ==============================================================================
def obter_dados_ifdata(trimestre, cnpj, relatorio_codigo):
    """
    Faz a requisição final cruzando o CNPJ da IF com o código do relatório.
    Exemplo de trimestre: '202603' (Março/2026)
    """
    url = f"{BASE_URL}/IfDataValores(anoMes=@anoMes,relatorio=@relatorio,cnpj=@cnpj)?@anoMes='{trimestre}'&@relatorio='{relatorio_codigo}'&@cnpj='{cnpj}'&$format=json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json().get('value', [])
        
        if not dados:
            return None
            
        return pd.DataFrame(dados)
    
    except Exception as e:
        print(f"Erro ao baixar {cnpj} (Relatório: {relatorio_codigo}): {e}")
        return None

# ==============================================================================
# EXECUÇÃO DO FLUXO (ORQUESTRADOR)
# ==============================================================================
if __name__ == "__main__":
    # Cria a pasta se não existir
    os.makedirs("ifdata", exist_ok=True)
    
    # 1. Atualiza os dicionários (Se já existirem, você pode pular essas funções)
    df_relatorios = obter_relatorios()
    df_ifs = obter_instituicoes_financeiras()
    
    # 2. Exemplo prático de cruzamento:
    # Vamos pegar o código do primeiro relatório e o CNPJ da primeira IF da lista
    relatorio_teste = df_relatorios['Nome'].iloc[0] # Ajuste o nome da coluna de acordo com o retorno da API
    cnpj_teste = df_ifs['Cnpj'].iloc[0] # Ajuste o nome da coluna Cnpj
    
    print(f"\n3. Testando extração: Relatório {relatorio_teste} para CNPJ {cnpj_teste}...")
    
    # O IFData funciona por trimestres (Março, Junho, Setembro, Dezembro).
    df_resultado = obter_dados_ifdata(trimestre="202512", cnpj=cnpj_teste, relatorio_codigo=relatorio_teste)
    
    if df_resultado is not None and not df_resultado.empty:
        print("-> Extração perfeita! Amostra dos dados:")
        print(df_resultado.head())
    else:
        print("-> Nenhum dado encontrado para esse cruzamento específico.")