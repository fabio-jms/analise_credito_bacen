import os
import zipfile
import json
import pandas as pd

# 1. Configuração de Caminhos usando a nova estrutura do projeto
pasta_scr_brutos = "dados_brutos_scrdata"
arquivo_zip_2026 = None

# Mecanismo defensivo para localizar o ZIP de 2026 na pasta de brutos
if os.path.exists(pasta_scr_brutos):
    arquivos_pasta = os.listdir(pasta_scr_brutos)
    zips_2026 = [f for f in arquivos_pasta if "2026" in f and f.endswith(".zip")]
    if zips_2026:
        # Pega o ZIP mais recente de 2026 encontrado
        arquivo_zip_2026 = os.path.join(pasta_scr_brutos, sorted(zips_2026)[-1])

# Caso o script seja executado de dentro da pasta scrdata/, ajusta o caminho relativo
if not arquivo_zip_2026 or not os.path.exists(arquivo_zip_2026):
    pasta_scr_brutos_alt = "dados_scr_brutos"
    if os.path.exists(pasta_scr_brutos_alt):
        zips_2026 = [f for f in os.listdir(pasta_scr_brutos_alt) if "2026" in f and f.endswith(".zip")]
        if zips_2026:
            arquivo_zip_2026 = os.path.join(pasta_scr_brutos_alt, sorted(zips_2026)[-1])

if not arquivo_zip_2026 or not os.path.exists(arquivo_zip_2026):
    print("Erro: O arquivo ZIP de microdados de 2026 não foi encontrado na pasta dados_scr_brutos!")
    print("Por favor, garanta que o arquivo .zip enviado pelo BACEN esteja na pasta correta.")
    exit()

print(f"=== LENDO MICRODADOS DO ZIP DE 2026 ===")
print(f"Arquivo mapeado: {arquivo_zip_2026}")

# ==============================================================================
# 2. ABRIR O ZIP E PROCESSAR O ARQUIVO INTEIRO EM BLOCOS (CHUNKS)
# ==============================================================================
csv_alvo = None
with zipfile.ZipFile(arquivo_zip_2026, "r") as z:
    lista_arquivos = z.namelist()
    arquivos_marco = [f for f in lista_arquivos if "202603" in f and f.endswith(".csv")]
    
    if not arquivos_marco:
        print("Erro: Não encontramos nenhum arquivo CSV de março de 2026 (202603) no ZIP!")
        exit()
        
    csv_alvo = arquivos_marco[0]
    print(f"Processando arquivo completo por blocos: {csv_alvo}...")

    # Inicializamos um dicionário de conjuntos (sets) vazios para acumular as categorias
    colunas_para_dicionario = ['data_base', 'uf', 'segmento', 'cliente', 'cnae_ocupacao', 'porte', 'modalidade', 'submodalidade', 'indexador']
    categorias_acumuladas = {col: set() for col in colunas_para_dicionario}

    with z.open(csv_alvo) as f:
        # Lendo em blocos de 150.000 linhas por vez (Garante uso mínimo de RAM)
        contador_blocos = 0
        for chunk in pd.read_csv(f, sep=";", chunksize=150000, encoding="utf-8", low_memory=False):
            contador_blocos += 1
            if contador_blocos % 5 == 0:
                print(f"  -> Processando bloco {contador_blocos} (linhas lidas: {contador_blocos * 150000:,})")

            # Padroniza os cabeçalhos do bloco atual
            chunk.columns = [col.lower().strip() for col in chunk.columns]

            # Varre as colunas selecionadas do bloco e adiciona os dados no conjunto global
            for col in colunas_para_dicionario:
                if col in chunk.columns:
                    # O .update() adiciona múltiplos valores de uma vez e remove duplicadas nativamente
                    valores_limpos = chunk[col].astype(str).str.strip().tolist()
                    categorias_acumuladas[col].update(valores_limpos)

# ==============================================================================
# 3. ESTRUTURAR O DICIONÁRIO DEFINITIVO (COM 100% DOS DADOS)
# ==============================================================================
print("\nConsolidando mapa final de metadados...")

descricoes_macro = {
    "data_base": "Data de fechamento do relatório do SCR (Referência: Março de 2026).",
    "uf": "Estado da federação de contratação do crédito.",
    "segmento": "Segmentação da instituição (Banco, Fintech, Cooperativa, etc.).",
    "cliente": "Tipo de pessoa do tomador (PF / PJ).",
    "cnae_ocupacao": "Classificação CNAE ocupação",
    "porte": "Porte do cliente (Faturamento/Renda).",
    "modalidade": "Tipo macro da operação financeira.",
    "submodalidade": "Detalhamento do produto de crédito (Essencial para isolar Cartões de Crédito).",
    "indexador": "Indicador econômico que corrige o contrato."
}

dicionario_marco = {}

for col in colunas_para_dicionario:
    # Transformamos o set de volta em uma lista ordenada para o JSON ficar legível
    lista_final_ordenada = sorted(list(categorias_acumuladas[col]))
    
    dicionario_marco[col] = {
        "tipo_tecnico": "string",  # Como lemos tudo como string para o set, padronizamos aqui
        "conceito": descricoes_macro.get(col, "Mapeamento descritivo estrutural."),
        "total_opcoes": len(lista_final_ordenada),
        "valores_aceitos": lista_final_ordenada
    }

# Salva o arquivo JSON atualizado na pasta scrdata/
caminho_json_saida = os.path.join("scrdata", "dicionario_descritivo_scr_202603.json") if "scrdata" not in os.getcwd() else "dicionario_descritivo_scr_202603.json"
with open(caminho_json_saida, "w", encoding="utf-8") as file_out:
    json.dump(dicionario_marco, file_out, indent=4, ensure_ascii=False)

print(f"-> [SUCESSO] Novo dicionário descritivo salvo em: {caminho_json_saida}")

# 4. Amostra Analítica para conferência no Terminal
print("\n=== ESTRUTURA DOS CAMPOS DESCRITIVOS LOCALIZADOS ===")
for campo, metadados in dicionario_marco.items():
    print(f"\n• Campo: {campo} ({metadados['total_opcoes']} categorias encontradas)")
    # Mostra até as 5 primeiras opções para conferência ágil
    print(f"  Valores de exemplo: {metadados['valores_aceitos'][:5]}...")