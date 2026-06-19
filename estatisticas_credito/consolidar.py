import os
import numpy as np  # Mover para cá! Carrega uma única vez e fica disponível para todo o script
import pandas as pd

# 1. Configurações de caminhos
pasta_dados = "dados_brutos"
arquivo_planilha = "codigos_series_bacen.csv"
arquivo_saida = "resumo_estatistico_credito.csv"

# Verificar se os arquivos necessários existem
if not os.path.exists(pasta_dados):
    print(f"Erro: A pasta '{pasta_dados}' não existe. Rode o 'main.py' primeiro!")
    exit()

if not os.path.exists(arquivo_planilha):
    print(f"Erro: A planilha '{arquivo_planilha}' não foi encontrada na raiz!")
    exit()

# 2. Criar um mapeamento (Dicionário) do Código para o Nome Completo da série
print(f"Carregando mapeamento de nomes a partir de: {arquivo_planilha}")
df_referencia = pd.read_csv(arquivo_planilha, sep=";")
df_referencia.columns = df_referencia.columns.str.strip()

# Criamos um dicionário onde a CHAVE é o Código e o VALOR é o Nome Completo
# Convertemos o CODIGO para string para evitar problemas de compatibilidade no mapeamento
mapa_nomes_completos = dict(zip(df_referencia["CODIGO"].astype(str), df_referencia["NOME"]))


# 3. Listar todos os arquivos CSV que estão dentro da pasta dados_brutos
arquivos = [f for f in os.listdir(pasta_dados) if f.endswith(".csv")]

if not arquivos:
    print(f"Aviso: Nenhum arquivo CSV encontrado dentro de '{pasta_dados}'.")
    exit()

print(f"Encontrados {len(arquivos)} arquivos. Iniciando consolidação com nomes completos...")

dados_consolidados = []

# 4. Varrer arquivo por arquivo de forma automática
for index, nome_arquivo in enumerate(arquivos):
    caminho_completo = os.path.join(pasta_dados, nome_arquivo)
    
    try:
        df = pd.read_csv(caminho_completo, sep=";")
        
        if df.empty or "valor" not in df.columns or "data" not in df.columns:
            continue
            
        if df["valor"].dtype == "object":
            df["valor"] = df["valor"].str.replace(",", ".").astype(float)
        else:
            df["valor"] = df["valor"].astype(float)
            
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df = df.sort_values(by="data").reset_index(drop=True)
        
        # --- EXTRAIR O CÓDIGO A PARTIR DO NOVO PADRÃO DE NOME ---
        # Exemplo: "ICC_27673_ICC_PF_CRDPESNAOCONSIGNADO.csv"
        nome_sem_extensao = nome_arquivo.replace(".csv", "")
        partes = nome_sem_extensao.split("_")
        
        # O código da série agora é a segunda parte (índice 1) devido à sua alteração!
        codigo_serie_str = partes[1]
        classe = partes[0]
        nome_abrev = "_".join(partes[2:]) if len(partes) > 2 else nome_sem_extensao

        # Buscar o Nome Completo no nosso mapa usando o código capturado
        # O .get() serve para trazer um texto padrão caso o código não seja achado na planilha
        nome_completo_serie = mapa_nomes_completos.get(codigo_serie_str, "Nome não encontrado na planilha")

        # --- REPLICAR OS CÁLCULOS (COM PROTEÇÃO CONTRA INFINITO) ---
        media_historica = df["valor"].mean()
        ultimo_valor = df["valor"].iloc[-1]
        ultima_data = df["data"].iloc[-1].strftime("%d/%m/%Y")
        
        id_maximo = df["valor"].idxmax()
        pico_valor = df["valor"].loc[id_maximo]
        pico_data = df["data"].loc[id_maximo].strftime("%d/%m/%Y")
        
        # Calcular as variações percentuais normais
        df["var_mensal"] = df["valor"].pct_change() * 100
        df["var_anual"] = df["valor"].pct_change(periods=12) * 100
        
        # --- TRUQUE DE PROTEÇÃO: Substituir 'inf' e '-inf' por zero (ou por vazio) ---
        # Usamos o método do Pandas .replace() para limpar as colunas calculadas
        df["var_mensal"] = df["var_mensal"].replace([np.inf, -np.inf], 0)
        df["var_anual"] = df["var_anual"].replace([np.inf, -np.inf], 0)
        
        # Agora pegamos os últimos valores com total segurança
        ultima_var_mensal = df["var_mensal"].iloc[-1]
        ultima_var_anual = df["var_anual"].iloc[-1]
        
        # 5. Guardar os dados com a nova coluna de Nome Completo
        resumo_serie = {
            "Código": codigo_serie_str,
            "Classe": classe,
            "Nome_Abreviado": nome_abrev,
            "Nome_Completo_SGS": nome_completo_serie,  # <- Nova coluna estratégica!
            "Ultima_Data": ultima_data,
            "Ultimo_Valor": ultimo_valor,
            "Var_Mensal_Pct": ultima_var_mensal,
            "Var_Anual_Pct": ultima_var_anual,
            "Media_Historica": media_historica,
            "Pico_Valor": pico_valor,
            "Pico_Data": pico_data
        }
        
        dados_consolidados.append(resumo_serie)
        print(f"[{index + 1}/{len(arquivos)}] Mapeado e Processado: Série {codigo_serie_str}")
        
    except Exception as e:
        print(f"  -> Erro ao processar o arquivo {nome_arquivo}: {e}")

# 6. Salvar relatório final consolidado dinamicamente com a data da carga
if dados_consolidados:
    df_final = pd.DataFrame(dados_consolidados)
    
    colunas_ordenadas = [
        "Código", "Classe", "Nome_Abreviado", "Nome_Completo_SGS", 
        "Ultima_Data", "Ultimo_Valor", "Var_Mensal_Pct", "Var_Anual_Pct", 
        "Media_Historica", "Pico_Valor", "Pico_Data"
    ]
    df_final = df_final[colunas_ordenadas]
    
    # --- LOGICA DE VERSIONAMENTO DINÂMICO ---
    # 1. Pegamos a maior data encontrada na coluna Ultima_Data (formato original: DD/MM/AAAA)
    # Convertemos temporariamente para o formato de data do Pandas para achar o valor máximo real
    datas_convertidas = pd.to_datetime(df_final["Ultima_Data"], format="%d/%m/%Y")
    maior_data = datas_convertidas.max()
    
    # 2. Formatamos essa maior data no padrão desejado: AAAAMM
    sufixo_data = maior_data.strftime("%Y%m")
    
    # 3. Montamos o nome do arquivo final com o carimbo de data (ex: resumo_estatistico_credito_202606.csv)
    arquivo_saida_dinamico = f"resumo_estatistico_credito_{sufixo_data}.csv"
    
    # 4. Salvamos a tabela com a formatação perfeita para o Excel
    df_final.to_csv(
        arquivo_saida_dinamico, 
        index=False, 
        sep=";", 
        encoding="utf-8-sig", 
        decimal=","
    )
    
    print("\n==================================================")
    print(f"SUCESSO! Relatório versionado gerado: {arquivo_saida_dinamico}")
    print(f"Total de {len(df_final)} séries consolidadas com a foto de {maior_data.strftime('%m/%Y')}!")
    print("==================================================")
else:
    print("\nNenhum dado pôde ser consolidado.")