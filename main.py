import datetime
import os
import time
import pandas as pd
import requests

# Configurações - Nome atualizado conforme solicitado!
arquivo_planilha = "codigos_series_bacen.csv"
pasta_destino = "dados_brutos"
arquivo_log = "execucao.log"


def registrar_log(mensagem):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    texto_formatado = f"[{timestamp}] {mensagem}"
    print(texto_formatado)
    with open(arquivo_log, "a", encoding="utf-8") as f:
        f.write(texto_formatado + "\n")


with open(arquivo_log, "w", encoding="utf-8") as f:
    f.write("=== INÍCIO DA EXECUÇÃO DO DOWNLOAD INCREMENTAL ===\n")

# Ler planilha
try:
    df_planilha = pd.read_csv(arquivo_planilha, sep=";")
    df_planilha.columns = df_planilha.columns.str.strip()
except Exception as e:
    registrar_log(f"ERRO CRÍTICO ao ler a planilha: {e}")
    exit()

if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)

lista_falhas = []


def executar_download_incremental(index, total, codigo, nome_arquivo, classe, tentativa=1):
    prefixo = f"Tentativa {tentativa}" if tentativa > 1 else f"{index + 1}/{total}"
    caminho_final = os.path.join(pasta_destino, f"{classe}_{codigo}_{nome_arquivo}.csv")

    # 1. Determinar se faremos carga FULL ou INCREMENTAL
    arquivo_existe = os.path.exists(caminho_final)

    if arquivo_existe:
        # Se já existe, pede apenas os últimos 3 meses (90 dias)
        data_limite = datetime.datetime.now() - datetime.timedelta(days=90)
        data_inicial_str = data_limite.strftime("%d/%m/%Y")
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={data_inicial_str}"
        tipo_carga = "INCREMENTAL (Últimos 3 meses)"
    else:
        # Se não existe, baixa tudo desde o começo do histórico
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"
        tipo_carga = "FULL (Histórico Completo)"

    registrar_log(f"[{prefixo}] [{tipo_carga}] {classe} -> {nome_arquivo} (Série {codigo})...")

    try:
        resposta = requests.get(url, timeout=15)

        if resposta.status_code == 200:
            dados_novos_json = resposta.json()
            df_novos = pd.DataFrame(dados_novos_json)

            if df_novos.empty:
                registrar_log("   -> Nenhum dado novo encontrado no período.")
                return True

            # 2. Se for incremental, mescla com o arquivo antigo
            if arquivo_existe:
                df_antigo = pd.read_csv(caminho_final, sep=";")

                # Junta as duas tabelas
                df_consolidado = pd.concat([df_antigo, df_novos], ignore_index=True)

                # Remove linhas duplicadas mantendo o dado mais recente
                df_consolidado = df_consolidado.drop_duplicates(subset=["data"], keep="last")
            else:
                df_consolidado = df_novos

            # 3. Salva o arquivo atualizado de volta na pasta
            df_consolidado.to_csv(caminho_final, index=False, sep=";")
            registrar_log(f"   -> SUCESSO! Arquivo atualizado. Total de registros: {len(df_consolidado)}")
            return True
        else:
            registrar_log(f"   -> INSUCESSO: Status {resposta.status_code}")
            return False

    except Exception as e:
        registrar_log(f"   -> FALHA: {e}")
        return False


# Primeira passada
total_series = len(df_planilha)
for index, linha in df_planilha.iterrows():
    codigo = linha["CODIGO"]
    nome_arquivo = linha["NOME_ABREV"]
    classe = linha["Classe"]

    sucesso = executar_download_incremental(index, total_series, codigo, nome_arquivo, classe)
    if not sucesso:
        lista_falhas.append(linha)

    time.sleep(0.5)

# Repescagem (Retry)
if lista_falhas:
    registrar_log(f"\n=== REPESCAGEM: {len(lista_falhas)} SÉRIES FALHARAM ===")
    time.sleep(3)
    for index, linha in enumerate(lista_falhas.copy()):
        codigo = linha["CODIGO"]
        nome_arquivo = linha["NOME_ABREV"]
        classe = linha["Classe"]

        sucesso_retry = executar_download_incremental(index, len(lista_falhas), codigo, nome_arquivo, classe, tentativa=2)
        if sucesso_retry:
            lista_falhas.remove(linha)
        time.sleep(0.5)

registrar_log("\n=== EXECUÇÃO CONCLUÍDA ===")
registrar_log(f"Pendências restantes: {len(lista_falhas)}")