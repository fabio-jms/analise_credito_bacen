import os
import pandas as pd

# 1. Definir qual arquivo queremos analisar
pasta_dados = "dados_brutos"
# Usando o novo padrão de nome (Classe_NOME_ABREV.csv)
nome_arquivo = "Saldo_SALDO_PF_TOTAL.csv" 
caminho_arquivo = os.path.join(pasta_dados, nome_arquivo)

# Verificar se o arquivo existe antes de continuar
if not os.path.exists(caminho_arquivo):
    print(f"Erro: O arquivo {caminho_arquivo} não foi encontrado. Rode o main.py primeiro!")
    exit()

# 2. Ler e tratar os dados (ajustando tipos que aprendemos antes)
df = pd.read_csv(caminho_arquivo, sep=";")

if df["valor"].dtype == "object":
    df["valor"] = df["valor"].str.replace(",", ".").astype(float)
else:
    df["valor"] = df["valor"].astype(float)

df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")

# Garantir que os dados estão ordenados por data cronológica (do mais antigo ao mais recente)
df = df.sort_values(by="data").reset_index(drop=True)


# 3. CÁLCULO DE ESTATÍSTICAS BÁSICAS
media_historica = df["valor"].mean()
ultimo_valor = df["valor"].iloc[-1]
ultima_data = df["data"].iloc[-1].strftime("%m/%Y")

# Encontrar o Pico Histórico (Valor Máximo) e a linha correspondente
id_maximo = df["valor"].idxmax() # Descobre o índice da linha do valor máximo
pico_valor = df["valor"].loc[id_maximo]
pico_data = df["data"].loc[id_maximo].strftime("%m/%Y")


# 4. CÁLCULO DE CRESCIMENTO PERCENTUAL
# O Pandas tem uma função fantástica chamada .pct_change() que calcula a variação percentual linha a linha
# Como os dados do BACEN costumam ser mensais, de uma linha para a outra temos a variação mensal (MoM)
df["variacao_mensal_pct"] = df["valor"].pct_change() * 100

# E se quisermos a variação em 12 meses (Ano contra Ano - YoY)? Basta pular 12 linhas para trás!
df["variacao_anual_pct"] = df["valor"].pct_change(periods=12) * 100

# Pegar os resultados mais recentes
ultima_var_mensal = df["variacao_mensal_pct"].iloc[-1]
ultima_var_anual = df["variacao_anual_pct"].iloc[-1]


# 5. EXIBIR O RELATÓRIO NA TELA
print("==================================================")
print(f"  RELATÓRIO ESTATÍSTICO: {nome_arquivo.upper()}")
print("==================================================")
print(f"Último Dado Disponível ({ultima_data}):")
print(f"  -> Saldo Atual: R$ {ultimo_valor:,.2f} Mi")
print(f"  -> Crescimento no mês (MoM): {ultima_var_mensal:+.2f}%")
print(f"  -> Crescimento em 12 meses (YoY): {ultima_var_anual:+.2f}%")
print("--------------------------------------------------")
print(f"Média Histórica do Período: R$ {media_historica:,.2f} Mi")
print("--------------------------------------------------")
print(f"Pico Histórico (Máximo):")
print(f"  -> Valor: R$ {pico_valor:,.2f} Mi")
print(f"  -> Data do recorde: {pico_data}")
print("==================================================")

# Opcional: Se quiser ver as últimas linhas com as novas colunas de cálculo
print("\nVisão recente da tabela calculada:")
print(df[["data", "valor", "variacao_mensal_pct", "variacao_anual_pct"]].tail(5))