import json
from datetime import date

import pandas as pd
import streamlit as st

import db
import stats

import sqlite3

# 1. Função para conectar ao banco de dados SQLite
def conectar_banco():
    # O 'dados_fc.db' é o arquivo do nosso banco de dados local
    conexao = sqlite3.connect("dados_fc.db")
    return conexao

# 2. Função para criar a tabela e aplicar a carga inicial (Seed)
def inicializar_banco_times():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Cria a tabela de times se ela ainda não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_time TEXT NOT NULL UNIQUE
        )
    """)

    # Lista padrão de times da família (você pode alterar ou adicionar mais depois)
    times_padrao = [
        ("Real Madrid",),
        ("Barcelona",),
        ("Manchester City",),
        ("Bayern de Munique",),
        ("Liverpool",),
        ("PSG",)
    ]

    # Verificamos se a tabela já possui algum time cadastrado
    cursor.execute("SELECT COUNT(*) FROM times")
    quantidade = cursor.fetchone()[0]

    # Se a tabela estiver vazia (quantidade == 0), injetamos a seed!
    if quantidade == 0:
        # executemany insere vários itens de uma vez só com segurança
        cursor.executemany("INSERT OR IGNORE INTO times (nome_time) VALUES (?)", times_padrao)
        conexao.commit()
        print("Carga inicial (Seed) de times realizada com sucesso!")

    # Fechamos a conexão para liberar recursos do sistema
    conexao.close()

# Executamos a função assim que o script é lido
inicializar_banco_times()


# Configuração da página
st.set_page_config(page_title="App FC Family", page_icon="⚽", layout="wide")
db.init_db()

st.title("⚽ App FC Family — Placar do Grupo")

# Abas do aplicativo
tabs = st.tabs(["🎮 Nova Partida", "🏆 Classificação", "📜 Histórico", "👤 Jogadores", "🏟️ Clubes / Países"])
tab_nova_partida, tab_ranking, tab_historico, tab_jogadores, tab_clubes = tabs


# =========================================================================
# 1. ABA: NOVA PARTIDA (Com Filtro por País/Liga Reativo e Definitivo)
# =========================================================================
with tab_nova_partida:
    st.header("Registrar Nova Partida")
    st.caption("Filtre o time pelo país de origem, informe os gols e salve.")

    players = db.list_players()
    todos_clubes = db.list_clubs()

    if not players or not todos_clubes:
        st.warning("⚠️ Cadastre pelo menos 2 jogadores e importe o arquivo de clubes/países antes de registrar uma partida.")
    else:
        # Extrai os países/ligas únicas em ordem alfabética do banco de dados
        ligas_disponiveis = sorted(list(set(c["league"] for c in todos_clubes)))

        col_casa, col_fora = st.columns(2)

        # --- MANDANTE (CASA) ---
        with col_casa:
            st.markdown("### 🏠 Mandante (Casa)")
            p_casa = st.selectbox("Jogador Casa", players, format_func=lambda x: x["name"], key="input_p_casa")
            
            # Seleção do País/Liga (chave limpa)
            liga_casa = st.selectbox("País / Liga (Casa)", ligas_disponiveis, key="liga_casa_sel")
            
            # FILTRAGEM REATIVA: Filtra apenas os times daquele país selecionado
            clubes_c = [c for c in todos_clubes if c["league"] == liga_casa]
            
            # CORREÇÃO CRUCIAL: Adicionamos o nome da liga na chave (`key`) do time. 
            # Isso força o Streamlit a destruir e recriar o selectbox sempre que você muda de país, matando o bug da África do Sul!
            clube_casa = st.selectbox(
                "Time (Casa)", 
                clubes_c, 
                format_func=lambda x: x["name"], 
                key=f"clube_casa_sel_{liga_casa}"
            )
            gols_casa = st.number_input("Gols (Casa)", min_value=0, step=1, value=0, key="input_gols_casa")

        # --- VISITANTE (FORA) ---
        with col_fora:
            st.markdown("### ✈️ Visitante (Fora)")
            p_fora = st.selectbox("Jogador Fora", players, format_func=lambda x: x["name"], key="input_p_fora")
            
            # Seleção do País/Liga
            liga_fora = st.selectbox("País / Liga (Fora)", ligas_disponiveis, key="liga_fora_sel")
            
            # FILTRAGEM REATIVA: Filtra apenas os times daquele país selecionado
            clubes_f = [c for c in todos_clubes if c["league"] == liga_fora]
            
            # CORREÇÃO CRUCIAL: Chave dinâmica baseada no país selecionado para evitar travamentos
            clube_fora = st.selectbox(
                "Time (Fora)", 
                clubes_f, 
                format_func=lambda x: x["name"], 
                key=f"clube_fora_sel_{liga_fora}"
            )
            gols_fora = st.number_input("Gols (Fora)", min_value=0, step=1, value=0, key="input_gols_fora")

        st.divider()
        
        # Botão fora de formulários engessados para dar total liberdade de reatividade aos selects acima
        if st.button("💾 Salvar Partida e Atualizar Ranking", use_container_width=True, type="primary"):
            if p_casa["id"] == p_fora["id"]:
                st.error("❌ O Jogador da Casa não pode ser o mesmo Jogador de Fora!")
            else:
                match_date = date.today().isoformat()
                entries = [
                    {"player_id": p_casa["id"], "club_id": clube_casa["id"], "side": "casa", "goals": int(gols_casa)},
                    {"player_id": p_fora["id"], "club_id": clube_fora["id"], "side": "fora", "goals": int(gols_fora)}
                ]
                db.create_match(match_date, "", entries)
                st.success("🎉 Partida registrada com sucesso!")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 Classificação Rápida do Grupo")
    if players:
        ranking_preview = stats.build_ranking(players, db.list_matches())
        df_prev = pd.DataFrame(ranking_preview)
        st.dataframe(df_prev[["Pos", "Jogador", "Pts", "J", "V", "E", "D", "SG"]], use_container_width=True, hide_index=True)


# =========================================================================
# 2. ABA: CLASSIFICAÇÃO COMPLETA
# =========================================================================
with tab_ranking:
    st.header("🏆 Classificação Geral (Pontos Corridos)")
    st.caption("Vitória = 3 pts · Empate = 1 pt · Derrota = 0 pts")

    players = db.list_players()
    matches = db.list_matches()

    if not players:
        st.info("Cadastre jogadores para gerar a tabela.")
    else:
        ranking = stats.build_ranking(players, matches)
        df = pd.DataFrame(ranking)
        st.dataframe(df, use_container_width=True, hide_index=True)


# =========================================================================
# 3. ABA: HISTÓRICO DE PARTIDAS
# =========================================================================
with tab_historico:
    st.header("📜 Histórico de Partidas")
    matches = db.list_matches()

    if not matches:
        st.info("Nenhuma partida registrada ainda.")
    else:
        for m in matches:
            label, _, _ = stats.match_result_label(m["entries"])
            with st.container(border=True):
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"**Data:** {m['match_date']}")
                    for e in m["entries"]:
                        side_icon = "🏠" if e["side"] == "casa" else "✈️"
                        st.text(f"{side_icon} {e['player_name']} ({e['club_name']} - {e['league']}) ➔ {e['goals']} gols")
                    st.markdown(f"**Placar Final:** {label}")
                with col_del:
                    if st.button("🗑️ Excluir", key=f"del_match_{m['id']}"):
                        db.delete_match(m["id"])
                        st.rerun()


# =========================================================================
# 4. ABA: GERENCIAR JOGADORES
# =========================================================================
with tab_jogadores:
    st.header("👤 Gerenciar Jogadores")

    with st.form("add_player_form", clear_on_submit=True):
        p_name = st.text_input("Nome / Apelido do jogador")
        if st.form_submit_button("Adicionar Jogador") and p_name.strip():
            db.add_player(p_name.strip())
            st.success(f"Jogador '{p_name.strip()}' adicionado!")
            st.rerun()

    players = db.list_players()
    if players:
        st.subheader("Cadastrados")
        for p in players:
            c1, c2 = st.columns([4, 1])
            c1.write(p["name"])
            if c2.button("Remover", key=f"del_p_{p['id']}"):
                db.delete_player(p["id"])
                st.rerun()


# =========================================================================
# 5. ABA: CLUBES E PAÍSES
# =========================================================================
with tab_clubes:
    st.header("🏟️ Clubes e Países")
    sub_import, sub_manual, sub_list = st.tabs(["📁 Importar CSV", "➕ Adicionar Manual", "📋 Ver Todos"])

    with sub_import:
        up_file = st.file_uploader("Arquivo CSV (ex: fc26_times_por_pais.csv)", type=["csv"])
        if up_file is not None:
            try:
                df_imp = pd.read_csv(up_file, sep=';')
                colunas_lower = {c.lower(): c for c in df_imp.columns}
                col_liga = colunas_lower.get("pais") or colunas_lower.get("liga") or colunas_lower.get("league")
                col_clube = colunas_lower.get("time") or colunas_lower.get("clube") or colunas_lower.get("club")

                if col_liga and col_clube:
                    cnt = 0
                    for _, row in df_imp.iterrows():
                        db.add_club(str(row[col_clube]), str(row[col_liga]))
                        cnt += 1
                    st.success(f"🎉 {cnt} times/países importados com sucesso!")
                else:
                    st.error("❌ O arquivo CSV precisa conter as colunas 'Pais' e 'Time' (ou 'Liga' e 'Clube').")
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

    with sub_manual:
        with st.form("add_club_form", clear_on_submit=True):
            c_name = st.text_input("Nome do Time/Clube")
            l_name = st.text_input("Nome do País/Liga")
            if st.form_submit_button("Adicionar Time") and c_name.strip() and l_name.strip():
                db.add_club(c_name.strip(), l_name.strip())
                st.success(f"Time '{c_name}' adicionado!")
                st.rerun()

    with sub_list:
        clubs = db.list_clubs()
        if clubs:
            st.dataframe(pd.DataFrame(clubs)[["name", "league"]].rename(columns={"name": "Time", "league": "País / Liga"}), use_container_width=True, hide_index=True)
            if st.button("🗑️ Limpar todos os times"):
                db.clear_clubs()
                st.rerun()
        else:
            st.info("Nenhum time cadastrado.")