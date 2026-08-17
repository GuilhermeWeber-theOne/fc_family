import os
import toml
import pandas as pd
from supabase import create_client, Client

# =========================================================================
# CONEXÃO SEGURA COM O SUPABASE
# =========================================================================
try:
    caminho_secrets = os.path.join(".streamlit", "secrets.toml")
    config = toml.load(caminho_secrets)
    
    url = config["supabase"]["SUPABASE_URL"]
    key = config["supabase"]["SUPABASE_KEY"]
    
    supabase: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
except Exception as e:
    print(f"❌ Erro crítico ao carregar credenciais: {e}")

def importar_clubes_em_lotes():
    arquivo_csv = "fc26_times_por_pais.csv"
    
    if not os.path.exists(arquivo_csv):
        print(f"❌ Erro: O arquivo '{arquivo_csv}' não foi encontrado na pasta atual!")
        return

    try:
        print(f"📂 Lendo o arquivo {arquivo_csv}...")
        # Lendo o CSV usando ponto e vírgula
        df = pd.read_csv(arquivo_csv, sep=";")
        
        # Padronizando as colunas estritamente para o padrão do banco (league, name)
        df = df.rename(columns={"Pais": "league", "Time": "name"})
        
        # Removendo eventuais linhas vazias para evitar lixo no banco
        df = df.dropna(subset=["name", "league"])
        
        dados_clubes = df.to_dict(orient="records")
        total_clubes = len(dados_clubes)
        print(f"🚀 Total de {total_clubes} clubes encontrados. Iniciando envio seguro...")

        # ENGENHARIA DE LOTES (BATCHING): Enviamos de 50 em 50 para nunca sobrecarregar a API
        tamanho_lote = 50
        sucessos = 0

        for i in range(0, total_clubes, tamanho_lote):
            lote = dados_clubes[i:i + tamanho_lote]
            try:
                # Enviando o lote atual para a tabela 'clubs'
                response = supabase.table("clubs").insert(lote).execute()
                sucessos += len(lote)
                print(f"📦 Progreso: {sucessos}/{total_clubes} clubes enviados com sucesso...")
            except Exception as erro_lote:
                print(f"⚠️ Aviso no lote do índice {i}: {erro_lote}")

        print("🎉 Processo de migração concluído com sucesso!")

    except Exception as e:
        print(f"❌ Erro geral durante a leitura ou envio do CSV: {e}")

if __name__ == "__main__":
    importar_clubes_em_lotes()
    