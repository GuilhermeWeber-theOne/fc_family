import os
import sqlite3
import pandas as pd

DB_NAME = "fc_family.db"

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar as colunas pelo nome (ex: row['name'])
    return conn

def init_db():
    """
    Inicializa o banco de dados, cria as tabelas necessárias 
    e aplica a carga inicial (Seed) dos times padrão se a tabela estiver vazia.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Jogadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Tabela de Clubes / Países
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            league TEXT NOT NULL
        )
    """)

    # Tabela de Partidas / Placares
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            player1 TEXT NOT NULL,
            player2 TEXT NOT NULL,
            score1 INTEGER NOT NULL,
            score2 INTEGER NOT NULL,
            team1 TEXT NOT NULL,
            team2 TEXT NOT NULL
        )
    """)

    conn.commit()

    # --- SEED AUTOMÁTICA DOS TIMES (Carga Inicial Padrão) ---
    # Verifica se a tabela de clubes está vazia
    cursor.execute("SELECT COUNT(*) FROM clubs")
    total_clubes = cursor.fetchone()[0]

    if total_clubes == 0:
        # Caminho do arquivo CSV padrão na raiz do projeto
        csv_path = "fc26_times_por_pais.csv"
        if os.path.exists(csv_path):
            try:
                # Lê o CSV usando o delimitador correto (ponto e vírgula)
                df_times = pd.read_csv(csv_path, sep=";")
                
                # Identifica as colunas de forma flexível (Pais / Time)
                colunas_lower = {col.lower().strip(): col for col in df_times.columns}
                col_liga = colunas_lower.get("pais") or colunas_lower.get("liga")
                col_clube = colunas_lower.get("time") or colunas_lower.get("clube") or colunas_lower.get("club")

                if col_liga and col_clube:
                    dados_para_inserir = []
                    for _, row in df_times.iterrows():
                        time_nome = str(row[col_clube]).strip()
                        liga_nome = str(row[col_liga]).strip()
                        dados_para_inserir.append((time_nome, liga_nome))
                    
                    # Insere todos os times de uma vez no banco com segurança
                    cursor.executemany("INSERT INTO clubs (name, league) VALUES (?, ?)", dados_para_inserir)
                    conn.commit()
                    print("Carga inicial (Seed) dos times padrão realizada com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar a seed automática de times: {e}")

    conn.close()

# Funções auxiliares de manipulação de dados

def add_player(name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Jogador já existe
    finally:
        conn.close()

def list_players():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM players ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]

def add_club(name, league):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clubs (name, league) VALUES (?, ?)", (name, league))
    conn.commit()
    conn.close()

def list_clubs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, league FROM clubs ORDER BY league ASC, name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"name": row["name"], "league": row["league"]} for row in rows]

def add_match(date, player1, player2, score1, score2, team1, team2):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO matches (date, player1, player2, score1, score2, team1, team2)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date, player1, player2, score1, score2, team1, team2))
    conn.commit()
    conn.close()

def list_matches():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, player1, player2, score1, score2, team1, team2 FROM matches ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]