def build_ranking(players, matches):
    """Agrega estatísticas de todos os jogadores cadastrados a partir das partidas.

    - Inclui todo jogador cadastrado, mesmo com 0 jogos.
    - Compatível com 'players' vindo como lista de strings ou de dicionários.
    - Critérios de desempate padrão de futebol: Pts -> V -> SG -> GM -> Nome.
    """
    stats_map = {}

    # Inicializa o dicionário de estatísticas para cada jogador cadastrado
    for p in players:
        # CORREÇÃO CIRÚRGICA: Verifica se 'p' é uma string pura ou um dicionário
        player_name = p if isinstance(p, str) else p.get("name")
        
        if player_name:
            stats_map[player_name] = {
                "Jogador": player_name,
                "Pts": 0,
                "J": 0,
                "V": 0,
                "E": 0,
                "D": 0,
                "GM": 0,
                "GS": 0,
                "SG": 0,
            }

    # Processa cada partida registrada
    for m in matches:
        entries = m["entries"]
        if len(entries) < 2:
            continue

        c_entry = next((e for e in entries if e["side"] == "casa"), None)
        f_entry = next((e for e in entries if e["side"] == "fora"), None)

        if not c_entry or not f_entry:
            continue

        p_casa = c_entry["player_name"]
        p_fora = f_entry["player_name"]
        g_casa = c_entry["goals"]
        g_fora = f_entry["goals"]

        # Garante que os jogadores da partida existam no mapa de stats
        for name in [p_casa, p_fora]:
            if name not in stats_map:
                stats_map[name] = {
                    "Jogador": name,
                    "Pts": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GM": 0, "GS": 0, "SG": 0
                }

        # Atualiza jogos e gols marcados/sofridos
        stats_map[p_casa]["J"] += 1
        stats_map[p_fora]["J"] += 1

        stats_map[p_casa]["GM"] += g_casa
        stats_map[p_casa]["GS"] += g_fora
        stats_map[p_fora]["GM"] += g_fora
        stats_map[p_fora]["GS"] += g_casa

        # Define pontos (Vitória = 3, Empate = 1, Derrota = 0)
        if g_casa > g_fora:
            stats_map[p_casa]["Pts"] += 3
            stats_map[p_casa]["V"] += 1
            stats_map[p_fora]["D"] += 1
        elif g_fora > g_casa:
            stats_map[p_fora]["Pts"] += 3
            stats_map[p_fora]["V"] += 1
            stats_map[p_casa]["D"] += 1
        else:
            stats_map[p_casa]["Pts"] += 1
            stats_map[p_casa]["E"] += 1
            stats_map[p_fora]["Pts"] += 1
            stats_map[p_fora]["E"] += 1

    # Calcula o Saldo de Gols (SG)
    for p_name, data in stats_map.items():
        data["SG"] = data["GM"] - data["GS"]

    # Converte em lista para ordenação
    rows = list(stats_map.values())

    # Ordenação oficial: Pontos -> Vitórias -> Saldo de Gols -> Gols Marcados -> Nome
    rows.sort(key=lambda x: (-x["Pts"], -x["V"], -x["SG"], -x["GM"], x["Jogador"]))

    # Atribui a posição na tabela (Pos)
    for index, r in enumerate(rows, start=1):
        r["Pos"] = index

    # Reordena as chaves para exibição limpa
    ordered_cols = ["Pos", "Jogador", "Pts", "J", "V", "E", "D", "GM", "GS", "SG"]
    return [{col: r[col] for col in ordered_cols} for r in rows]
