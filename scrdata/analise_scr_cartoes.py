import os
import zipfile
import pandas as pd

# 1. Configurações de caminhos
pasta_dados_scr = "dados_scr_brutos"
nome_zip = "scrdata_2025.zip"
caminho_zip = os.path.join(pasta_dados_scr, nome_zip)

if not os.path.exists(caminho_zip):
    print(f"Erro: O arquivo {caminho_zip} não foi encontrado. Execute o main_scr.py primeiro!")
    exit()

# 2. Definição dos filtros ajustados e validados para o padrão AAAA-MM-DD
datas_alvo = ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"]

submodalidades_cartao = [
    "Cartão de crédito - compra à vista e parcelado lojista",
    "Cartão de crédito - compra ou fatura parcelada pela instituição financeira emitente do cartão",
    "Cartão de crédito - compra, fatura parcelada ou saque financiado pela instituição financeira emitente do cartão",
    "Cartão de crédito - não migrado"
]

segmentos_alvo = ["Banco", "Fintech"]

# Extrair 'AAAAMM' dinamicamente a partir do padrão AAAA-MM-DD
sufixos_meses_alvo = [data.split("-")[0] + data.split("-")[1] for data in datas_alvo]

print("Iniciando mapeamento cirúrgico dos arquivos de interesse dentro do ZIP...")
blocos_consolidados = []

# 3. Abrir o pacote ZIP do SCR
with zipfile.ZipFile(caminho_zip, 'r') as z:
    lista_arquivos = z.namelist()
    
    # Filtrar a lista interna para ler apenas os CSVs dos meses desejados
    arquivos_para_rodar = []
    for arquivo in lista_arquivos:
        if (arquivo.lower().endswith('.csv') or arquivo.lower().endswith('.txt')) and any(sufixo in arquivo for sufixo in sufixos_meses_alvo):
            arquivos_para_rodar.append(arquivo)
            
    print(f"Arquivos mapeados para leitura direta ({len(arquivos_para_rodar)} de {len(lista_arquivos)}):")
    for arq in arquivos_para_rodar:
        print(f"  -> {arq}")
    
    # --- LOOP DE ALTA PERFORMANCE ---
    for arquivo_interno in arquivos_para_rodar:
        print(f"\nProcessando partição alvo: {arquivo_interno}...")
        
        with z.open(arquivo_interno) as f:
            # Processamento em chunks de 100.000 linhas
            for chunk in pd.read_csv(f, sep=";", chunksize=100000, encoding="utf-8", low_memory=False):
                
                # Padronizar cabeçalhos para letras minúsculas e sem espaços
                chunk.columns = [col.lower().strip() for col in chunk.columns]
                
                # PROGRAMAÇÃO DEFENSIVA: Remover espaços em branco invisíveis do conteúdo textual das colunas chaves
                chunk['data_base'] = chunk['data_base'].astype(str).str.strip()
                chunk['submodalidade'] = chunk['submodalidade'].astype(str).str.strip()
                chunk['segmento'] = chunk['segmento'].astype(str).str.strip()
                
                # Se este bloco específico não contiver nenhuma das nossas datas alvo, pula para o próximo chunk
                if not chunk['data_base'].isin(datas_alvo).any():
                    continue
                
                # Aplicar os filtros estritos cruzados
                filtro_estrito = (
                    chunk['data_base'].isin(datas_alvo) &
                    chunk['submodalidade'].isin(submodalidades_cartao) &
                    chunk['segmento'].isin(segmentos_alvo)
                )
                
                df_filtrado = chunk[filtro_estrito].copy()
                
                if not df_filtrado.empty:
                    # --- TRATAMENTO ULTRA-PROTEGIDO DOS CAMPOS FINANCEIROS ---
                    for col_valor in ['carteira_ativa', 'carteira_inadimplencia']:
                        # Nova abordagem: se NÃO for numérico (seja object ou string), aplica a higienização
                        if not pd.api.types.is_numeric_dtype(df_filtrado[col_valor]):
                            df_filtrado[col_valor] = df_filtrado[col_valor].astype(str).str.strip().str.replace('"', '', regex=False)
                            df_filtrado[col_valor] = df_filtrado[col_valor].str.replace(".", "", regex=False)
                            df_filtrado[col_valor] = df_filtrado[col_valor].str.replace(",", ".", regex=False)
                        
                        # Converte com segurança para float real
                        df_filtrado[col_valor] = pd.to_numeric(df_filtrado[col_valor], errors='coerce')
                    
                    # Preenche eventuais nulos remanescentes com zero antes de acumular
                    df_filtrado['carteira_ativa'] = df_filtrado['carteira_ativa'].fillna(0)
                    df_filtrado['carteira_inadimplencia'] = df_filtrado['carteira_inadimplencia'].fillna(0)
                    
                    blocos_consolidados.append(
                        df_filtrado[['data_base', 'uf', 'segmento', 'carteira_ativa', 'carteira_inadimplencia']]
                    )

# 4. COMPILAÇÃO E CÁLCULO DA TAXA DE INADIMPLÊNCIA FINAL
if blocos_consolidados:
    df_final_scr = pd.concat(blocos_consolidados, ignore_index=True)
    
    print("\nConsolidando volumes globais e agregando resultados...")
    # Agrupamento por Data, Estado e Segmento
    df_agrupado = df_final_scr.groupby(['data_base', 'uf', 'segmento']).sum().reset_index()
    
    # Cálculo preciso da inadimplência (carteira inadimplência / carteira ativa)
    df_agrupado['inadimplencia_pct'] = (df_agrupado['carteira_inadimplencia'] / df_agrupado['carteira_ativa']).fillna(0) * 100
    df_agrupado['inadimplencia_pct'] = df_agrupado['inadimplencia_pct'].round(2)
    
    # Ordenação lógica completa
    df_agrupado = df_agrupado.sort_values(by=['data_base', 'uf', 'segmento']).reset_index(drop=True)
    
    arquivo_saida = "resultado_inadimplencia_scr_2025.csv"
    df_agrupado.to_csv(arquivo_saida, index=False, sep=";", encoding="utf-8-sig")
    
    print("\n==================================================")
    print("      PROCESSAMENTO V2 INTEGRAL CONCLUÍDO!        ")
    print("==================================================")
    print(f"Arquivo gerado com sucesso: {arquivo_saida}")
    print(f"Total de registros no relatório: {len(df_agrupado)}")
    print("\nAmostra das primeiras linhas do resultado:")
    print(df_agrupado.head(15))
    print("==================================================")
else:
    print("\n[Erro] Nenhum bloco de dados pôde ser consolidado. Verifique os filtros.")