import os
import sqlite3
import pandas as pd

DB_NAME = "fc_family.db"

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn

def init_db():
    """
    Inicializa o banco de dados, cria as tabelas e faz a carga inicial automática (Seed)
    dos times a partir do arquivo CSV embutido no projeto, sem exigir upload manual.
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

    # Tabela de Partidas
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

    # Tabela de Detalhes da Partida (Entradas normalizadas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            side TEXT NOT NULL, -- 'casa' ou 'fora'
            team TEXT NOT NULL,
            goals INTEGER NOT NULL,
            FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed automático dos clubes se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM clubs")
    count = cursor.fetchone()[0]
    if count == 0:
        csv_path = "fc26_times_por_pais.csv"
        if os.path.exists(csv_path):
            try:
                # O delimitador do seu CSV é ponto e vírgula (;)
                df_csv = pd.read_csv(csv_path, sep=";")
                for _, row in df_csv.iterrows():
                    # Suporta chaves em inglês ou português ('club' ou 'clube', 'league' ou 'pais')
                    league_val = row.get("league") or row.get("Pais") or "Desconhecido"
                    name_val = row.get("club") or row.get("clube") or row.get("Time") or "Desconhecido"
                    cursor.execute(
                        "INSERT INTO clubs (name, league) VALUES (?, ?)",
                        (str(name_val).strip(), str(league_val).strip())
                    )
                conn.commit()
            except Exception as e:
                print(f"Erro ao carregar o CSV automático: {e}")

    conn.close()

def add_player(name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def update_player(old_name, new_name):
    """Atualiza o nome de um jogador existente no banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE players SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def delete_player(name):
    """Exclui um jogador do banco de dados pelo nome."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE name = ?", (name,))
    conn.commit()
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
    match_id = cursor.lastrowid

    # Inserções normalizadas para as estatísticas
    cursor.execute("""
        INSERT INTO match_entries (match_id, player_name, side, team, goals)
        VALUES (?, ?, 'casa', ?, ?)
    """, (match_id, player1, team1, score1))

    cursor.execute("""
        INSERT INTO match_entries (match_id, player_name, side, team, goals)
        VALUES (?, ?, 'fora', ?, ?)
    """, (match_id, player2, team2, score2))

    conn.commit()
    conn.close()

def list_matches():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches ORDER BY id DESC")
    match_rows = cursor.fetchall()

    matches = []
    for m in match_rows:
        m_id = m["id"]
        cursor.execute("SELECT player_name, side, team, goals FROM match_entries WHERE match_id = ?", (m_id,))
        entries = [dict(row) for row in cursor.fetchall()]
        
        matches.append({
            "id": m_id,
            "date": m["date"],
            "entries": entries
        })
    conn.close()
    return matches
