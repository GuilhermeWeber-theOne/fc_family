import os
import toml
import pandas as pd
from supabase import create_client, Client

# Lendo as credenciais de segurança do arquivo secrets.toml
try:
    caminho_secrets = os.path.join(".streamlit", "secrets.toml")
    config = toml.load(caminho_secrets)
    
    url = config["supabase"]["SUPABASE_URL"]
    key = config["supabase"]["SUPABASE_KEY"]
    
    # Criando o cliente de conexão com o Supabase
    supabase: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
except Exception as e:
    print(f"❌ Erro ao ler credenciais ou conectar: {e}")

def importar_csv_para_supabase():
    arquivo_csv = "fc26_times_por_pais.csv"
    
    try:
        print(f"📂 Lendo o arquivo {arquivo_csv}...")
        # Lendo o CSV utilizando o delimitador ponto e vírgula
        df = pd.read_csv(arquivo_csv, sep=";")
        
        # Padronizando as colunas para corresponderem às da tabela 'clubs' no Supabase
        df = df.rename(columns={"Pais": "league", "Time": "name"})
        
        # Convertendo o DataFrame do pandas em uma lista de dicionários padrão do Python
        dados_clubes = df.to_dict(orient="records")
        
        print(f"🚀 Enviando {len(dados_clubes)} clubes para o Supabase... Aguarde.")
        
        # CORREÇÃO CIRÚRGICA: Chamamos explicitamente .table("clubs") antes de inserir
        response = supabase.table("clubs").insert(dados_clubes).execute()
        
        print("🎉 Sucesso absoluto! Todos os clubes foram importados para o Supabase!")
        
    except Exception as e:
        print(f"❌ Erro durante a importação do CSV: {e}")

if __name__ == "__main__":
    importar_csv_para_supabase()