import streamlit as st
import sqlite3

# ==========================================
# 1. CAMADA DE BANCO DE DADOS (O Cofre)
# ==========================================

def conectar_banco():
    """
    Cria e retorna a conexão com o banco de dados local SQLite.
    """
    conexao = sqlite3.connect("dados_fc.db")
    return conexao

def inicializar_banco_times():
    """
    Cria a tabela de times caso ela não exista e aplica a carga inicial (seed)
    com os times padrão da família se a tabela estiver vazia.
    """
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Criação da tabela de times
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_time TEXT NOT NULL UNIQUE
        )
    """)

    # Lista padrão de times da família
    times_padrao = [
        ("Real Madrid",),
        ("Barcelona",),
        ("Manchester City",),
        ("Bayern de Munique",),
        ("Liverpool",),
        ("PSG",)
    ]

    # Verifica se já existem times cadastrados para evitar duplicação
    cursor.execute("SELECT COUNT(*) FROM times")
    quantidade = cursor.fetchone()[0]

    # Se estiver vazio, injeta os times padrão (Seed)
    if quantidade == 0:
        cursor.executemany("INSERT OR IGNORE INTO times (nome_time) VALUES (?)", times_padrao)
        conexao.commit()
        print("Carga inicial (Seed) de times realizada com sucesso!")

    conexao.close()

def carregar_times():
    """
    Busca todos os times cadastrados no banco de dados e os retorna
    em formato de lista limpa para o Streamlit.
    """
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT nome_time FROM times ORDER BY nome_time ASC")
    times_brutos = cursor.fetchall()
    
    conexao.close()
    
    # Transforma a lista de tuplas em uma lista simples de textos
    lista_times = [time[0] for time in times_brutos]
    return lista_times


# Inicializa o banco e a seed logo na abertura do app
inicializar_banco_times()


# ==========================================
# 2. CAMADA DE INTERFACE VISUAL (A Vitrine)
# ==========================================

st.title("⚽ App FC Family - Gestão de Campeonatos")
st.write("Bem-vindo ao painel oficial do nosso campeonato!")

# Carrega os times do banco de dados
times_no_banco = carregar_times()

st.subheader("Times Cadastrados no Sistema:")

# Validação visual na tela
if len(times_no_banco) > 0:
    for time in times_no_banco:
        st.write(f"✔️ {time}")
else:
    st.warning("Nenhum time cadastrado no momento.")
    