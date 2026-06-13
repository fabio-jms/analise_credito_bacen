import os
import pandas as pd

# 1. Configurações de caminhos
pasta_dados = "dados_brutos"
arquivo_saida = "resumo_estatistico_credito.csv"

# Verificar se a pasta de dados brutos existe
if not os.path.exists(pasta_dados):
    print(f"Erro: A pasta '{pasta_dados}' não existe. Rode o 'main.py' primeiro!")
    exit()

# 2. Listar todos os arquivos CSV que estão dentro da pasta dados_brutos
arquivos = [f for f in os.listdir(pasta_dados) if f.endswith(".csv")]

if not arquivos:
    print(f"Aviso: Nenhum arquivo CSV encontrado dentro de '{pasta_dados}'.")
    exit()

print(f"Encontrados {len(arquivos)} arquivos para processar. Iniciando consolidação...")

# Lista onde guardaremos o dicionário de resumo de cada arquivo
dados_consolidados = []

# 3. Varrer arquivo por arquivo de forma automática
for index, nome_arquivo in enumerate(arquivos):
    caminho_completo = os.path.join(pasta_dados, nome_arquivo)
    
    try:
        # Ler o arquivo atual
        df = pd.read_csv(caminho_completo, sep=";")
        
        # Pular arquivos que por acaso estejam vazios
        if df.empty or "valor" not in df.columns or "data" not in df.columns:
            continue
            
        # Tratar os dados da coluna valor e data
        if df["valor"].dtype == "object":
            df["valor"] = df["valor"].str.replace(",", ".").astype(float)
        else:
            df["valor"] = df["valor"].astype(float)
            
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df = df.sort_values(by="data").reset_index(drop=True)
        
        # Separar a Classe e o Nome_Abrev a partir do nome do arquivo (ex: Saldo_credito_pessoa_fisica.csv)
        # O .replace(".csv", "") remove a extensão e o .split("_", 1) quebra no primeiro underline
        nome_sem_extensao = nome_arquivo.replace(".csv", "")
        partes = nome_sem_extensao.split("_", 1)
        classe = partes[0]
        nome_abrev = partes[1] if len(partes) > 1 else nome_sem_extensao

        # --- REPLICAR OS CÁLCULOS PARA CADA SÉRIE ---
        media_historica = df["valor"].mean()
        ultimo_valor = df["valor"].iloc[-1]
        ultima_data = df["data"].iloc[-1].strftime("%d/%m/%Y")
        
        # Pico histórico
        id_maximo = df["valor"].idxmax()
        pico_valor = df["valor"].loc[id_maximo]
        pico_data = df["data"].loc[id_maximo].strftime("%d/%m/%Y")
        
        # Variações percentuais (Mensal e Anual)
        df["var_mensal"] = df["valor"].pct_change() * 100
        df["var_anual"] = df["valor"].pct_change(periods=12) * 100
        
        ultima_var_mensal = df["var_mensal"].iloc[-1]
        ultima_var_anual = df["var_anual"].iloc[-1]
        
        # 4. Guardar os indicadores calculados estruturados em um dicionário
        resumo_serie = {
            "Classe": classe,
            "Nome_Abreviado": nome_abrev,
            "Ultima_Data": ultima_data,
            "Ultimo_Valor": ultimo_valor,
            "Var_Mensal_Pct": ultima_var_mensal,
            "Var_Anual_Pct": ultima_var_anual,
            "Media_Historica": media_historica,
            "Pico_Valor": pico_valor,
            "Pico_Data": pico_data
        }
        
        dados_consolidados.append(resumo_serie)
        print(f"[{index + 1}/{len(arquivos)}] Processado com sucesso: {nome_arquivo}")
        
    except Exception as e:
        print(f"  -> Erro ao processar o arquivo {nome_arquivo}: {e}")

# 5. Transformar a lista de resumos em uma tabela final do Pandas e salvar
if dados_consolidados:
    df_final = pd.DataFrame(dados_consolidados)
    
    # Salvamos usando ponto e vírgula (sep=";") porque o Excel em português abre direto de forma correta!
    df_final.to_csv(arquivo_saida, index=False, sep=";")
    
    print("\n==================================================")
    print(f"SUCESSO! Relatório consolidado gerado: {arquivo_saida}")
    print(f"Total de séries resumidas: {len(df_final)}")
    print("==================================================")
else:
    print("\nNenhum dado pôde ser consolidado.")