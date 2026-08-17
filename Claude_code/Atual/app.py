import json
from datetime import date

import pandas as pd
import streamlit as st

import db
import stats

# Configuração da página
st.set_page_config(page_title="App FC Family", page_icon="⚽", layout="wide")
#db.init_db()

st.title("⚽ App FC Family — Placar do Grupo")

# Abas do aplicativo (Restauradas e preservadas integralmente)
tabs = st.tabs(["🎮 Nova Partida", "🏆 Classificação", "📜 Histórico", "👤 Jogadores", "🏟️ Clubes / Países", "🔐 Admin"])
tab_nova_partida, tab_ranking, tab_historico, tab_jogadores, tab_clubes, tab_admin = tabs


# =========================================================================
# 1. ABA: NOVA PARTIDA (Com Filtro por País/Liga Reativo e Prévia do Ranking)
# =========================================================================
with tab_nova_partida:
    st.header("Registrar Nova Partida")
    st.caption("Filtre o time pelo país de origem, informe os gols e salve.")

    players = db.list_players()
    todos_clubes = db.list_clubs()

    if not players or not todos_clubes:
        st.warning("⚠️ Cadastre pelo menos 2 jogadores e aguarde o carregamento dos clubes/países antes de registrar uma partida.")
    else:
        # Extrai os países/ligas únicas em ordem alfabética
        ligas_disponiveis = sorted(list(set(c["league"] for c in todos_clubes)))

        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("### Jogador Casa")
            player1 = st.selectbox("Selecione o Jogador da Casa", players, key="p1_select")
            
            liga1 = st.selectbox("País / Liga (Casa)", ligas_disponiveis, key="liga1_select")
            times_liga1 = sorted([c["name"] for c in todos_clubes if c["league"] == liga1])
            team1 = st.selectbox("Time (Casa)", times_liga1, key="team1_select")
            
            score1 = st.number_input("Gols (Casa)", min_value=0, step=1, key="score1_input")

        with col_p2:
            st.markdown("### Jogador Fora")
            # Remove o player1 para evitar partida de um jogador contra si mesmo
            players_p2 = [p for p in players if p != player1]
            player2 = st.selectbox("Selecione o Jogador de Fora", players_p2 if players_p2 else players, key="p2_select")
            
            liga2 = st.selectbox("País / Liga (Fora)", ligas_disponiveis, key="liga2_select")
            times_liga2 = sorted([c["name"] for c in todos_clubes if c["league"] == liga2])
            team2 = st.selectbox("Time (Fora)", times_liga2, key="team2_select")
            
            score2 = st.number_input("Gols (Fora)", min_value=0, step=1, key="score2_input")

        match_date = st.date_input("Data da Partida", value=date.today())

        if st.button("💾 Salvar Partida", type="primary"):
            if player1 == player2:
                st.error("❌ Um jogador não pode jogar contra si mesmo!")
            else:
                db.add_match(
                    date=str(match_date),
                    player1=player1,
                    player2=player2,
                    score1=int(score1),
                    score2=int(score2),
                    team1=team1,
                    team2=team2
                )
                st.success(f"Partida salva com sucesso: {player1} ({score1}) x ({score2}) {player2}!")
                st.rerun()

    # --- PRÉVIA DA CLASSIFICAÇÃO NA TELA INICIAL ---
    st.markdown("---")
    st.subheader("🔥 Prévia do Top Ranking")
    
    all_players = db.list_players()
    all_matches = db.list_matches()
    ranking_data = stats.build_ranking(all_players, all_matches)
    
    if ranking_data:
        df_ranking = pd.DataFrame(ranking_data).head(5)
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma partida registrada ainda para gerar o ranking.")
    st.markdown("---")


# =========================================================================
# 2. ABA: CLASSIFICAÇÃO (Tabela Completa)
# =========================================================================
with tab_ranking:
    st.header("🏆 Tabela de Classificação Geral")
    st.caption("Critérios: Pontos Corridos -> Vitórias -> Saldo de Gols -> Gols Marcados -> Ordem Alfabética.")

    players = db.list_players()
    matches = db.list_matches()
    ranking = stats.build_ranking(players, matches)

    if ranking:
        df = pd.DataFrame(ranking)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Cadastre jogadores e registre partidas para visualizar a classificação completa.")


# =========================================================================
# 3. ABA: HISTÓRICO DE PARTIDAS
# =========================================================================
with tab_historico:
    st.header("📜 Histórico de Partidas Realizadas")
    matches = db.list_matches()

    if matches:
        for m in matches:
            label, winner, totals = stats.match_result_label(m["entries"])
            entries = m["entries"]
            
            c_entry = next((e for e in entries if e["side"] == "casa"), {"player_name": "?", "team": "?", "goals": 0})
            f_entry = next((e for e in entries if e["side"] == "fora"), {"player_name": "?", "team": "?", "goals": 0})

            with st.expander(f"📅 {m['date']} | {c_entry['player_name']} ({c_entry['team']}) {c_entry['goals']} x {f_entry['goals']} {f_entry['player_name']} ({f_entry['team']})"):
                st.write(f"**Data:** {m['date']}")
                st.write(f"🏠 **Casa:** {c_entry['player_name']} usando **{c_entry['team']}** — **{c_entry['goals']} gols**")
                st.write(f"✈️ **Fora:** {f_entry['player_name']} usando **{f_entry['team']}** — **{f_entry['goals']} gols**")
    else:
        st.info("Nenhuma partida registrada no histórico.")


# =========================================================================
# 4. ABA: JOGADORES
# =========================================================================
with tab_jogadores:
    st.subheader("👥 Gerenciamento de Jogadores")

with st.form("form_jogador"):
    novo_jogador = st.text_input("Nome do Novo Jogador")
    cadastrar = st.form_submit_button("Cadastrar Jogador")
    
    if cadastrar:
        if novo_jogador.strip():
            sucesso = db.add_player(novo_jogador.strip())
            if sucesso:
                st.success(f"Jogador '{novo_jogador.strip()}' cadastrado com sucesso na nuvem!")
                st.rerun()
        else:
            st.warning("Digite um nome válido para o jogador.")

st.subheader("Jogadores Cadastrados:")
players = db.list_players()
if players:
    for p in players:
        st.write(f"👤 {p}")
else:
    st.info("Nenhum jogador cadastrado ainda.")


# =========================================================================
# 5. ABA: CLUBES / PAÍSES
# =========================================================================
with tab_clubes:
    st.header("🏟️ Clubes e Países Disponíveis")
    st.caption("Estes times foram carregados automaticamente pelo sistema a partir da base oficial do projeto.")

    clubs = db.list_clubs()
    if clubs:
        df_clubs = pd.DataFrame(clubs).rename(columns={"name": "Clube / Time", "league": "País / Liga"})
        st.dataframe(df_clubs, use_container_width=True)
    else:
        st.warning("Nenhum clube encontrado no banco de dados.")


# =========================================================================
# 6. ABA: ADMINISTRAÇÃO (Protegida por Senha - Restaurada e Segura)
# =========================================================================
with tab_admin:
    st.header("🔐 Painel do Administrador")
    st.caption("Área restrita para correção de cadastros e gerenciamento do sistema.")

    # Lê a senha salva de forma segura no secrets.toml do Streamlit (padrão '123456')
    senha_cadastrada = st.secrets.get("admin_password", "123456")

    senha_digitada = st.text_input("Digite a senha de administrador:", type="password", key="admin_password_input")

    if senha_digitada == senha_cadastrada:
        st.success("✅ Acesso autorizado!")
        st.markdown("---")

        st.subheader("✏️ Gerenciar Jogadores (Editar ou Excluir)")
        jogadores_atuais = db.list_players()

        if jogadores_atuais:
            jogador_selecionado = st.selectbox("Selecione o jogador:", jogadores_atuais, key="admin_select_player")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### Alterar Nome do Jogador")
                novo_nome_input = st.text_input("Novo nome:", value=jogador_selecionado, key="admin_novo_nome")
                if st.button("Salvar Alteração", key="btn_save_player"):
                    if novo_nome_input.strip() and novo_nome_input.strip() != jogador_selecionado:
                        db.update_player(jogador_selecionado, novo_nome_input.strip())
                        st.success(f"Jogador '{jogador_selecionado}' renomeado para '{novo_nome_input.strip()}' com sucesso!")
                        st.rerun()
                    else:
                        st.warning("Digite um nome novo e válido.")

            with col2:
                st.markdown("##### Excluir Jogador")
                st.warning("⚠️ Cuidado: Isso pode afetar partidas antigas vinculadas a ele.")
                if st.button("🗑️ Excluir Jogador Permanentemente", type="primary", key="btn_delete_player"):
                    db.delete_player(jogador_selecionado)
                    st.success(f"Jogador '{jogador_selecionado}' excluído com sucesso!")
                    st.rerun()
        else:
            st.info("Não há jogadores cadastrados para gerenciar.")

    elif senha_digitada:
        st.error("❌ Senha incorreta. Acesso negado.")
    else:
        st.info("🔒 Por favor, insira a senha de administrador para desbloquear as ferramentas de edição.")
        