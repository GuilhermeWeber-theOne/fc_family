def match_side_totals(entries):
    """Soma os gols por lado (casa/fora) a partir das entradas de uma partida."""
    totals = {"casa": 0, "fora": 0}
    for e in entries:
        totals[e["side"]] += e["goals"]
    return totals


def match_result_label(entries):
    """Retorna string tipo 'Casa 3 x 1 Fora' e o lado vencedor ('casa','fora' ou 'empate')."""
    totals = match_side_totals(entries)
    if totals["casa"] > totals["fora"]:
        winner = "casa"
    elif totals["fora"] > totals["casa"]:
        winner = "fora"
    else:
        winner = "empate"
    label = f"Casa {totals['casa']} x {totals['fora']} Fora"
    return label, winner, totals


def build_ranking(players, matches):
    """Agrega estatísticas de todos os jogadores cadastrados a partir das partidas.

    - Inclui todo jogador cadastrado, mesmo com 0 jogos (como uma tabela de
      campeonato desde a rodada zero).
    - Pontos corridos: vitória = 3, empate = 1, derrota = 0.
    - Critérios de desempate (padrão de tabelas de futebol):
      1º Pontos, 2º Vitórias, 3º Saldo de Gols, 4º Gols Marcados, 5º Nome (A-Z).
    - Retorna já com a coluna 'Pos' (1º ao Nº lugar).
    """
    agg = {
        p["name"]: {
            "jogos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
            "gols_marcados": 0, "gols_sofridos": 0,
        }
        for p in players
    }

    for m in matches:
        entries = m["entries"]
        if not entries:
            continue
        totals = match_side_totals(entries)
        for e in entries:
            player = e["player_name"]
            if player not in agg:
                # segurança: jogador removido do cadastro mas presente em partida antiga
                agg[player] = {
                    "jogos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
                    "gols_marcados": 0, "gols_sofridos": 0,
                }
            side = e["side"]
            other_side = "fora" if side == "casa" else "casa"
            s = agg[player]
            s["jogos"] += 1
            s["gols_marcados"] += e["goals"]
            s["gols_sofridos"] += totals[other_side]
            if totals[side] > totals[other_side]:
                s["vitorias"] += 1
            elif totals[side] < totals[other_side]:
                s["derrotas"] += 1
            else:
                s["empates"] += 1

    rows = []
    for player, s in agg.items():
        saldo = s["gols_marcados"] - s["gols_sofridos"]
        pontos = s["vitorias"] * 3 + s["empates"]
        rows.append({
            "Jogador": player,
            "Pts": pontos,
            "J": s["jogos"],
            "V": s["vitorias"],
            "E": s["empates"],
            "D": s["derrotas"],
            "GM": s["gols_marcados"],
            "GS": s["gols_sofridos"],
            "SG": saldo,
        })

    # Desempate: Pontos > Vitórias > Saldo de Gols > Gols Marcados > Nome (A-Z)
    rows.sort(key=lambda r: (-r["Pts"], -r["V"], -r["SG"], -r["GM"], r["Jogador"]))

    for i, r in enumerate(rows, start=1):
        r["Pos"] = i

    # Reordena as chaves para exibição: Pos primeiro
    ordered_cols = ["Pos", "Jogador", "Pts", "J", "V", "E", "D", "GM", "GS", "SG"]
    return [{col: r[col] for col in ordered_cols} for r in rows]


def head_to_head(matches, player_a, player_b):
    """Calcula o retrospecto direto entre dois jogadores (apenas partidas em
    que estiveram em lados opostos). Usado no dashboard de comparação."""
    result = {
        "jogos": 0, "vitorias_a": 0, "empates": 0, "vitorias_b": 0,
        "gols_a": 0, "gols_b": 0,
    }
    for m in matches:
        entries = m["entries"]
        sides = {"casa": set(), "fora": set()}
        for e in entries:
            sides[e["side"]].add(e["player_name"])

        side_a = "casa" if player_a in sides["casa"] else ("fora" if player_a in sides["fora"] else None)
        side_b = "casa" if player_b in sides["casa"] else ("fora" if player_b in sides["fora"] else None)

        # só conta se os dois estavam na partida, em lados opostos
        if side_a is None or side_b is None or side_a == side_b:
            continue

        totals = match_side_totals(entries)
        result["jogos"] += 1
        result["gols_a"] += totals[side_a]
        result["gols_b"] += totals[side_b]
        if totals[side_a] > totals[side_b]:
            result["vitorias_a"] += 1
        elif totals[side_a] < totals[side_b]:
            result["vitorias_b"] += 1
        else:
            result["empates"] += 1
    return result
