import json
from datetime import date

import pandas as pd
import streamlit as st

import db
import stats

st.set_page_config(page_title="FutMatch PS5", page_icon="⚽", layout="centered")
db.init_db()

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ---------------------------------------------------------------
# Estilo (aproxima o visual do mockup: cartões escuros, cantos
# arredondados, caixas travadas para clube padrão)
# ---------------------------------------------------------------
st.markdown("""
<style>
.locked-box {
    background: #1a1a1d;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
}
.locked-label {
    color: #888;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.locked-value {
    font-size: 1.05rem;
    font-weight: 600;
}
.placar-x {
    text-align: center;
    padding-top: 1.7rem;
    font-weight: 700;
    font-size: 1.1rem;
}
div.stButton > button[kind="primary"] {
    border-radius: 12px;
    height: 3rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.title("⚽ FutMatch — Placar do Grupo (PS5)")


# ---------------------------------------------------------------
# Helpers reutilizados entre abas
# ---------------------------------------------------------------

def get_admin_password():
    try:
        return st.secrets.get("admin_password", "admin123")
    except Exception:
        return "admin123"


def pick_club(clubs, key, default_club_id=None, disabled=False):
    """Seletor em cascata: primeiro a Liga, depois o Clube daquela liga.
    Retorna o club_id escolhido (ou None se não houver clubes cadastrados)."""
    if not clubs:
        st.warning("Nenhum clube cadastrado. Peça a um administrador para importar clubes.")
        return None

    leagues = sorted(set(c["league"] for c in clubs))
    default_league = None
    if default_club_id:
        default_league = next((c["league"] for c in clubs if c["id"] == default_club_id), None)
    liga_index = leagues.index(default_league) if default_league in leagues else 0
    liga = st.selectbox("Liga", options=leagues, index=liga_index, key=f"{key}_liga", disabled=disabled)

    clubes_da_liga = [c for c in clubs if c["league"] == liga]
    ids = [c["id"] for c in clubes_da_liga]
    names = {c["id"]: c["name"] for c in clubes_da_liga}
    default_index = ids.index(default_club_id) if default_club_id in ids else 0
    club_id = st.selectbox(
        "Clube", options=ids, index=default_index,
        format_func=lambda x: names[x], key=f"{key}_clube", disabled=disabled,
    )
    return club_id


def render_locked_club(club_id, clubs):
    """Mostra o clube padrão do jogador como um cartão travado (só leitura)."""
    club = next((c for c in clubs if c["id"] == club_id), None)
    if club:
        st.markdown(f"""
        <div class="locked-box">
            <div class="locked-label">{club['league']}</div>
            <div class="locked-value">{club['name']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="locked-box">
            <div class="locked-label">Clube padrão</div>
            <div class="locked-value">Não definido</div>
        </div>
        """, unsafe_allow_html=True)


def render_ranking_table(players, matches):
    """Tabela de classificação completa, usada na aba Início e na aba Classificação."""
    if not players:
        st.info("Cadastre jogadores para gerar a tabela de classificação.")
        return

    ranking = stats.build_ranking(players, matches)
    df = pd.DataFrame(ranking)

    def highlight_leader(row):
        if row["Pos"] == 1 and row["J"] > 0:
            style = (
                "background: linear-gradient(90deg, "
                "rgba(255,255,255,0.18), rgba(255,255,255,0.02)); "
                "font-weight: 700;"
            )
            return [style] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_leader, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pos": st.column_config.NumberColumn("Pos", width="small"),
            "Pts": st.column_config.NumberColumn("Pts", width="small"),
        },
    )
    st.caption(
        "J = Jogos · V = Vitórias · E = Empates · D = Derrotas · "
        "GM = Gols Marcados · GS = Gols Sofridos · SG = Saldo de Gols · "
        "Pts = Pontos.  Desempate: Pts → V → SG → GM → nome (A-Z)."
    )


# ---------------------------------------------------------------
# Navegação em abas
# ---------------------------------------------------------------
tab_inicio, tab_partidas, tab_classificacao, tab_jogadores, tab_admin = st.tabs(
    ["🏠 Início", "📋 Partidas", "🏆 Classificação", "👤 Jogadores", "🔐 Administração"]
)


# ---------------------------------------------------------------
# ABA: INÍCIO — registro rápido (1x1) + classificação completa
# ---------------------------------------------------------------
with tab_inicio:
    st.subheader("Registrar Partida")

    players = db.list_players()
    clubs = db.list_clubs()

    if not players:
        st.warning("Nenhum jogador cadastrado ainda. Peça a um administrador para cadastrar (aba Administração).")
    else:
        player_names = {p["id"]: p["name"] for p in players}

        col_m, col_v = st.columns(2)
        with col_m:
            st.caption("MANDANTE")
            pid_casa = st.selectbox("Jogador (mandante)", options=list(player_names),
                                     format_func=lambda x: player_names[x], key="ini_p_casa",
                                     label_visibility="collapsed")
        with col_v:
            st.caption("VISITANTE")
            pid_fora = st.selectbox("Jogador (visitante)", options=list(player_names),
                                     format_func=lambda x: player_names[x], key="ini_p_fora",
                                     label_visibility="collapsed")

        player_casa = db.get_player(pid_casa)
        player_fora = db.get_player(pid_fora)

        col_m2, col_g1, col_x, col_g2, col_v2 = st.columns([2.2, 1, 0.5, 1, 2.2])

        update_default_casa = False
        update_default_fora = False

        with col_m2:
            if st.session_state.is_admin:
                club_casa = pick_club(clubs, "ini_casa", default_club_id=player_casa["default_club_id"])
                update_default_casa = st.checkbox("Definir como padrão", key="ini_upd_casa")
            else:
                club_casa = player_casa["default_club_id"]
                render_locked_club(club_casa, clubs)

        with col_g1:
            gols_casa = st.number_input("Gols mandante", min_value=0, value=0,
                                         key="ini_gols_casa", label_visibility="collapsed")
        with col_x:
            st.markdown('<div class="placar-x">X</div>', unsafe_allow_html=True)
        with col_g2:
            gols_fora = st.number_input("Gols visitante", min_value=0, value=0,
                                         key="ini_gols_fora", label_visibility="collapsed")

        with col_v2:
            if st.session_state.is_admin:
                club_fora = pick_club(clubs, "ini_fora", default_club_id=player_fora["default_club_id"])
                update_default_fora = st.checkbox("Definir como padrão", key="ini_upd_fora")
            else:
                club_fora = player_fora["default_club_id"]
                render_locked_club(club_fora, clubs)

        if pid_casa == pid_fora:
            st.error("Escolha jogadores diferentes para mandante e visitante.")
        elif club_casa is None or club_fora is None:
            st.warning(
                "Um dos jogadores ainda não tem clube padrão definido. "
                "Peça a um administrador para configurar em 'Administração → Clubes padrão'."
            )
        else:
            if st.button("⚡ Computar e Sincronizar", type="primary", use_container_width=True):
                db.create_match(date.today().isoformat(), "", [
                    {"player_id": pid_casa, "club_id": club_casa, "side": "casa", "goals": gols_casa},
                    {"player_id": pid_fora, "club_id": club_fora, "side": "fora", "goals": gols_fora},
                ])
                if update_default_casa:
                    db.set_player_default_club(pid_casa, club_casa)
                if update_default_fora:
                    db.set_player_default_club(pid_fora, club_fora)
                st.success("Partida registrada e classificação sincronizada!")
                st.rerun()

    st.divider()
    st.subheader("Classificação Completa")
    render_ranking_table(db.list_players(), db.list_matches())


# ---------------------------------------------------------------
# ABA: PARTIDAS — histórico + registro avançado (admin, 2x2+)
# ---------------------------------------------------------------
with tab_partidas:
    st.subheader("Histórico de partidas")
    matches = db.list_matches()

    if not matches:
        st.info("Nenhuma partida registrada ainda.")
    else:
        for m in matches:
            label, winner, totals = stats.match_result_label(m["entries"])
            with st.expander(f"📅 {m['match_date']} — {label}" + (f" ({m['note']})" if m["note"] else "")):
                casa = [e for e in m["entries"] if e["side"] == "casa"]
                fora = [e for e in m["entries"] if e["side"] == "fora"]
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Mandante**")
                    for e in casa:
                        st.write(f"{e['player_name']} — {e['club_name']} — {e['goals']} gol(s)")
                with col2:
                    st.markdown("**Visitante**")
                    for e in fora:
                        st.write(f"{e['player_name']} — {e['club_name']} — {e['goals']} gol(s)")
                if st.session_state.is_admin and st.button("🗑️ Excluir partida", key=f"del_match_{m['id']}"):
                    db.delete_match(m["id"])
                    st.rerun()

    st.divider()
    st.subheader("Registro avançado (2x2 ou mais)")

    if not st.session_state.is_admin:
        st.info(
            "Registro avançado (times com mais de 1 jogador por lado, ou clube "
            "diferente do padrão) é restrito a administradores. Entre na aba "
            "'Administração' com a senha para liberar."
        )
    else:
        players = db.list_players()
        clubs = db.list_clubs()

        if not players or not clubs:
            st.warning("Cadastre jogadores e clubes antes de registrar uma partida avançada.")
        else:
            player_names = {p["id"]: p["name"] for p in players}
            match_date = st.date_input("Data da partida", value=date.today(), key="adv_date")
            note = st.text_input("Observação (opcional)", key="adv_note",
                                  placeholder="Ex: Torneio da noite, ida/volta, etc.")

            st.markdown("**Lado Casa**")
            n_casa = st.number_input("Quantos jogadores no lado Casa?", min_value=1, max_value=4, value=1, key="adv_n_casa")
            casa_entries = []
            for i in range(int(n_casa)):
                c1, c2 = st.columns(2)
                pid = c1.selectbox(f"Jogador (Casa #{i+1})", options=list(player_names),
                                    format_func=lambda x: player_names[x], key=f"adv_casa_p_{i}")
                cid = c2.container()
                with cid:
                    club_id = pick_club(clubs, f"adv_casa_c_{i}")
                gols = st.number_input(f"Gols (Casa #{i+1})", min_value=0, value=0, key=f"adv_casa_g_{i}")
                casa_entries.append({"player_id": pid, "club_id": club_id, "side": "casa", "goals": gols})

            st.markdown("**Lado Fora**")
            n_fora = st.number_input("Quantos jogadores no lado Fora?", min_value=1, max_value=4, value=1, key="adv_n_fora")
            fora_entries = []
            for i in range(int(n_fora)):
                c1, c2 = st.columns(2)
                pid = c1.selectbox(f"Jogador (Fora #{i+1})", options=list(player_names),
                                    format_func=lambda x: player_names[x], key=f"adv_fora_p_{i}")
                cid = c2.container()
                with cid:
                    club_id = pick_club(clubs, f"adv_fora_c_{i}")
                gols = st.number_input(f"Gols (Fora #{i+1})", min_value=0, value=0, key=f"adv_fora_g_{i}")
                fora_entries.append({"player_id": pid, "club_id": club_id, "side": "fora", "goals": gols})

            all_entries = casa_entries + fora_entries
            label, winner, totals = stats.match_result_label(all_entries)
            st.info(f"Placar atual: **{label}**")

            if st.button("💾 Salvar partida avançada", type="primary"):
                used_players = [e["player_id"] for e in all_entries]
                if len(used_players) != len(set(used_players)):
                    st.error("Um mesmo jogador não pode aparecer duas vezes na mesma partida.")
                else:
                    db.create_match(match_date.isoformat(), note, all_entries)
                    st.success("Partida avançada salva com sucesso!")
                    st.rerun()


# ---------------------------------------------------------------
# ABA: CLASSIFICAÇÃO — tabela completa e detalhada
# ---------------------------------------------------------------
with tab_classificacao:
    st.subheader("🏆 Classificação do grupo")
    st.caption("Atualizada em tempo real, por pontos corridos (V=3 · E=1 · D=0).")
    render_ranking_table(db.list_players(), db.list_matches())


# ---------------------------------------------------------------
# ABA: JOGADORES — dashboard individual e confronto direto
# ---------------------------------------------------------------
with tab_jogadores:
    st.subheader("Dashboard do Jogador")
    players = db.list_players()

    if not players:
        st.info("Cadastre jogadores primeiro (aba Administração).")
    else:
        matches = db.list_matches()
        ranking = stats.build_ranking(players, matches)
        ranking_by_name = {r["Jogador"]: r for r in ranking}
        names = [p["name"] for p in players]

        selected = st.selectbox("Selecione um jogador", options=names, key="dash_player")
        r = ranking_by_name[selected]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Posição", f"{r['Pos']}º")
        c2.metric("Pontos", r["Pts"])
        c3.metric("Jogos", r["J"])
        c4.metric("Saldo de Gols", r["SG"])

        c5, c6, c7 = st.columns(3)
        c5.metric("Vitórias", r["V"])
        c6.metric("Empates", r["E"])
        c7.metric("Derrotas", r["D"])

        st.divider()
        st.markdown("**Confronto direto contra cada jogador**")

        rows = []
        for other in names:
            if other == selected:
                continue
            h2h = stats.head_to_head(matches, selected, other)
            if h2h["jogos"] == 0:
                continue
            rows.append({
                "Adversário": other,
                "Jogos": h2h["jogos"],
                "Vitórias": h2h["vitorias_a"],
                "Empates": h2h["empates"],
                "Derrotas": h2h["vitorias_b"],
                "Gols Marcados": h2h["gols_a"],
                "Gols Sofridos": h2h["gols_b"],
                "Saldo": h2h["gols_a"] - h2h["gols_b"],
            })

        if rows:
            df_h2h = pd.DataFrame(rows).sort_values("Jogos", ascending=False)
            st.dataframe(df_h2h, use_container_width=True, hide_index=True)
        else:
            st.info(f"{selected} ainda não enfrentou nenhum outro jogador cadastrado.")


# ---------------------------------------------------------------
# ABA: ADMINISTRAÇÃO — login + gestão de jogadores, clubes padrão e catálogo
# ---------------------------------------------------------------
with tab_admin:
    st.subheader("Administração")

    if not st.session_state.is_admin:
        st.caption(
            "Área restrita: só o administrador pode cadastrar jogadores, definir "
            "os clubes padrão de cada um e importar/editar o catálogo de clubes e ligas."
        )
        pwd = st.text_input("Senha de administrador", type="password", key="admin_pwd_input")
        if st.button("Entrar"):
            if pwd == get_admin_password():
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    else:
        st.success("Modo administrador ativo.")
        if st.button("Sair do modo administrador"):
            st.session_state.is_admin = False
            st.rerun()

        tab_players, tab_default, tab_clubs = st.tabs(["Jogadores", "Clubes padrão", "Clubes / Ligas"])

        # ---- Jogadores ----
        with tab_players:
            with st.form("add_player_admin", clear_on_submit=True):
                name = st.text_input("Nome / apelido do jogador")
                submitted = st.form_submit_button("Adicionar")
                if submitted and name.strip():
                    db.add_player(name)
                    st.success(f"Jogador '{name}' adicionado.")
                    st.rerun()

            players = db.list_players()
            if players:
                st.markdown("**Jogadores cadastrados**")
                for p in players:
                    c1, c2 = st.columns([4, 1])
                    c1.write(p["name"])
                    if c2.button("Remover", key=f"admin_del_player_{p['id']}"):
                        db.delete_player(p["id"])
                        st.rerun()
            else:
                st.info("Nenhum jogador cadastrado ainda.")

        # ---- Clubes padrão por jogador ----
        with tab_default:
            players = db.list_players()
            clubs = db.list_clubs()
            if not players:
                st.info("Cadastre jogadores primeiro na aba 'Jogadores'.")
            elif not clubs:
                st.info("Cadastre ou importe clubes primeiro na aba 'Clubes / Ligas'.")
            else:
                player_names = {p["id"]: p["name"] for p in players}
                pid = st.selectbox("Jogador", options=list(player_names),
                                    format_func=lambda x: player_names[x], key="admin_default_player")
                player = db.get_player(pid)
                club_id = pick_club(clubs, "admin_default", default_club_id=player["default_club_id"])
                if st.button("💾 Salvar clube padrão"):
                    db.set_player_default_club(pid, club_id)
                    st.success(f"Clube padrão de {player_names[pid]} atualizado.")
                    st.rerun()

                st.divider()
                st.markdown("**Clubes padrão atuais**")
                for p in players:
                    club = next((c for c in clubs if c["id"] == p["default_club_id"]), None)
                    club_label = f"{club['name']} ({club['league']})" if club else "— não definido —"
                    st.write(f"**{p['name']}**: {club_label}")

        # ---- Clubes / Ligas (catálogo) ----
        with tab_clubs:
            st.caption(
                "Importe sua lista de clubes do FC 26 via CSV ou JSON. "
                "Formato CSV: colunas 'club' e 'league'. "
                "Formato JSON: lista de objetos {\"club\": ..., \"league\": ...}."
            )

            sub_import, sub_manual, sub_list = st.tabs(["Importar arquivo", "Adicionar manual", "Lista atual"])

            with sub_import:
                uploaded = st.file_uploader("Selecione um arquivo CSV ou JSON", type=["csv", "json"])
                if uploaded is not None:
                    try:
                        if uploaded.name.endswith(".csv"):
                            df = pd.read_csv(uploaded)
                            rows = df.rename(columns=str.lower).to_dict(orient="records")
                        else:
                            rows = json.load(uploaded)
                        rows = [{"club": r["club"], "league": r["league"]} for r in rows]
                        st.write(f"{len(rows)} clubes encontrados no arquivo.")
                        if st.button("Importar para o app"):
                            db.bulk_add_clubs(rows)
                            st.success("Clubes importados com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao ler arquivo: {e}")

                st.divider()
                st.caption("Baixe um template para editar com a sua lista completa do FC 26:")
                template_csv = "club,league\nReal Madrid,La Liga\nManchester City,Premier League\nFlamengo,Brasileirão\n"
                st.download_button(
                    "Baixar template CSV", data=template_csv,
                    file_name="clubes_template.csv", mime="text/csv",
                )

            with sub_manual:
                with st.form("add_club", clear_on_submit=True):
                    club_name = st.text_input("Nome do clube")
                    league_name = st.text_input("Liga")
                    submitted = st.form_submit_button("Adicionar clube")
                    if submitted and club_name.strip() and league_name.strip():
                        db.add_club(club_name, league_name)
                        st.success(f"Clube '{club_name}' adicionado à liga '{league_name}'.")

            with sub_list:
                clubs = db.list_clubs()
                if clubs:
                    st.dataframe(
                        pd.DataFrame(clubs)[["name", "league"]].rename(
                            columns={"name": "Clube", "league": "Liga"}),
                        use_container_width=True, hide_index=True,
                    )
                    if st.button("🗑️ Limpar todos os clubes"):
                        db.clear_clubs()
                        st.rerun()
                else:
                    st.info("Nenhum clube cadastrado ainda. Importe um arquivo na aba ao lado.")

        st.divider()
        st.caption(
            f"Senha de administrador atual: `{'personalizada (via secrets.toml)' if get_admin_password() != 'admin123' else 'admin123 (padrão — recomendado trocar)'}`. "
            "Veja o TUTORIAL.md para configurar uma senha própria."
        )
