import streamlit as st
from supabase import create_client, Client

# =========================================================================
# CONEXÃO SEGURA COM O SUPABASE
# =========================================================================
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
    """Retorna a lista de nomes de jogadores cadastrados no Supabase."""
    try:
        response = supabase.table("players").select("name").execute()
        if response.data:
            return [player["name"] for player in response.data]
        return []
    except Exception as e:
        st.error(f"Erro ao listar jogadores: {e}")
        return []

def add_player(name: str):
    """Adiciona um novo jogador na tabela 'players'."""
    try:
        supabase.table("players").insert({"name": name.strip()}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar jogador: {e}")
        return False

# =========================================================================
# 2. FUNÇÕES DE CLUBES / TIMES
# =========================================================================

def list_clubs():
    """Retorna a lista de clubes salvos na tabela 'clubs'."""
    try:
        response = supabase.table("clubs").select("name, league").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao listar clubes: {e}")
        return []

def save_clubs_bulk(clubs_list):
    """Salva uma lista inteira de clubes em lote no Supabase."""
    try:
        supabase.table("clubs").upsert(clubs_list).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar clubes em lote: {e}")
        return False

# =========================================================================
# 3. FUNÇÕES DE PARTIDAS E PLACARES (MATCHES) - ADICIONADAS AGORA
# =========================================================================

def list_matches():
    """Retorna todas as partidas cadastradas na tabela 'matches' do Supabase."""
    try:
        response = supabase.table("matches").select("*").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao listar partidas: {e}")
        return []

def add_match(player1, player2, club1, club2, score1, score2, winner):
    """Salva uma nova partida com os placares e o vencedor na nuvem."""
    try:
        match_data = {
            "player1": player1,
            "player2": player2,
            "club1": club1,
            "club2": club2,
            "score1": int(score1),
            "score2": int(score2),
            "winner": winner
        }
        supabase.table("matches").insert(match_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar partida: {e}")
        return False
    