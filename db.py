import sqlite3
from contextlib import contextmanager

DB_PATH = "futmatch.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            league TEXT NOT NULL,
            UNIQUE(name, league)
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_date TEXT NOT NULL,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS match_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
            player_id INTEGER NOT NULL REFERENCES players(id),
            club_id INTEGER NOT NULL REFERENCES clubs(id),
            side TEXT NOT NULL CHECK(side IN ('casa','fora')),
            goals INTEGER NOT NULL DEFAULT 0
        );
        """)
        # Migração segura: adiciona coluna default_club_id se ainda não existir
        # (necessário para bancos criados antes desta versão do app)
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(players)")]
        if "default_club_id" not in cols:
            conn.execute("ALTER TABLE players ADD COLUMN default_club_id INTEGER REFERENCES clubs(id)")


# ---------- Players ----------

def add_player(name):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO players(name) VALUES (?)", (name.strip(),))


def list_players():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM players ORDER BY name")]


def set_player_default_club(player_id, club_id):
    with get_conn() as conn:
        conn.execute("UPDATE players SET default_club_id=? WHERE id=?", (club_id, player_id))


def get_player(player_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
        return dict(row) if row else None


def delete_player(player_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM players WHERE id=?", (player_id,))


# ---------- Clubs ----------

def add_club(name, league):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO clubs(name, league) VALUES (?,?)",
            (name.strip(), league.strip()),
        )


def bulk_add_clubs(rows):
    """rows: list of dicts with keys 'club' and 'league'"""
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO clubs(name, league) VALUES (?,?)",
            [(r["club"].strip(), r["league"].strip()) for r in rows],
        )


def list_clubs():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM clubs ORDER BY league, name")]


def list_clubs_by_league(league):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM clubs WHERE league=? ORDER BY name", (league,)
        )]


def list_leagues():
    with get_conn() as conn:
        return [r["league"] for r in conn.execute("SELECT DISTINCT league FROM clubs ORDER BY league")]


def clear_clubs():
    with get_conn() as conn:
        conn.execute("DELETE FROM clubs")


# ---------- Matches ----------

def create_match(match_date, note, entries):
    """entries: list of dicts {player_id, club_id, side, goals}"""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO matches(match_date, note) VALUES (?,?)", (match_date, note)
        )
        match_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO match_entries(match_id, player_id, club_id, side, goals) VALUES (?,?,?,?,?)",
            [(match_id, e["player_id"], e["club_id"], e["side"], e["goals"]) for e in entries],
        )
        return match_id


def delete_match(match_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM matches WHERE id=?", (match_id,))


def list_matches():
    with get_conn() as conn:
        matches = [dict(r) for r in conn.execute(
            "SELECT * FROM matches ORDER BY match_date DESC, id DESC"
        )]
        for m in matches:
            entries = conn.execute("""
                SELECT me.*, p.name as player_name, c.name as club_name, c.league as league
                FROM match_entries me
                JOIN players p ON p.id = me.player_id
                JOIN clubs c ON c.id = me.club_id
                WHERE me.match_id = ?
                ORDER BY me.side, me.id
            """, (m["id"],)).fetchall()
            m["entries"] = [dict(e) for e in entries]
        return matches


def get_all_entries():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT me.*, p.name as player_name, m.match_date as match_date
            FROM match_entries me
            JOIN players p ON p.id = me.player_id
            JOIN matches m ON m.id = me.match_id
        """).fetchall()
        return [dict(r) for r in rows]
