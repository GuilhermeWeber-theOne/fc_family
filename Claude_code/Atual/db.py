import streamlit as st
from supabase import create_client, Client

# =========================================================================
# CONEXÃO SEGURA COM O SUPABASE
# =========================================================================
# Buscamos as credenciais que você salvou no arquivo .streamlit/secrets.toml
# O Streamlit lê isso de forma segura através do st.secrets.
try:
    url: str = st.secrets["supabase"]["SUPABASE_URL"]
    key: str = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase. Verifique suas credenciais no secrets.toml: {e}")

# =========================================================================
# 1. FUNÇÕES DE JOGADORES
# =========================================================================

def list_players():
    """
    Retorna uma lista com os nomes de todos os jogadores cadastrados no Supabase.
    Mantém a mesma compatibilidade que o app.py já espera.
    """
    try:
        response = supabase.table("players").select("name").execute()
        # O Supabase retorna um objeto contendo a propriedade .data com a lista de dicionários
        if response.data:
            return [player["name"] for player in response.data]
        return []
    except Exception as e:
        st.error(f"Erro ao listar jogadores: {e}")
        return []

def add_player(name: str):
    """
    Adiciona um novo jogador na tabela 'players' do Supabase.
    """
    try:
        # Inserindo o registro na tabela
        supabase.table("players").insert({"name": name.strip()}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar jogador: {e}")
        return False

# =========================================================================
# 2. FUNÇÕES DE CLUBES / TIMES
# =========================================================================

def list_clubs():
    """
    Retorna a lista de clubes salvos na tabela 'clubs' do Supabase.
    """
    try:
        response = supabase.table("clubs").select("name, league").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao listar clubes: {e}")
        return []

def save_clubs_bulk(clubs_list):
    """
    Salva uma lista inteira de clubes de uma vez só no Supabase 
    (Útil para carregar o arquivo CSV padrão de fábrica).
    """
    try:
        # O Supabase permite inserir uma lista de dicionários de uma vez
        supabase.table("clubs").upsert(clubs_list).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar clubes em lote: {e}")
        return False
