# FutMatch — Placar do Grupo (PS5 / FC 26)

App web em Python (Streamlit) para registrar partidas locais do FC 26 jogadas em grupo,
calcular vitórias/derrotas/empates, saldo de gols e ranking geral.

## 1. Rodar localmente (teste rápido)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Isso abre o app em `http://localhost:8501` no seu navegador (funciona também acessando
esse endereço de outro celular na mesma rede Wi-Fi, trocando `localhost` pelo IP da máquina).

## 2. Publicar com link para o grupo (recomendado)

Opção gratuita e simples: **Streamlit Community Cloud**.

**Passo a passo:**
1. Crie um repositório no GitHub e suba os arquivos: `app.py`, `db.py`, `stats.py`, `requirements.txt`.
2. Acesse https://share.streamlit.io e conecte sua conta do GitHub.
3. Clique em "New app", selecione o repositório e o arquivo `app.py`.
4. Clique em "Deploy". Em ~1 minuto você recebe um link público (ex: `https://futmatch.streamlit.app`).
5. Compartilhe esse link com o grupo — todos acessam pelo navegador do celular, sem instalar nada.

> ⚠️ Nota sobre dados: o banco SQLite (`futmatch.db`) fica no servidor do app. No plano
> gratuito do Streamlit Cloud, o armazenamento é persistente entre acessos, mas pode ser
> resetado se o app ficar muito tempo inativo ou for reiniciado. Para um grupo casual isso
> costuma ser suficiente; se quiser durabilidade garantida a longo prazo, é possível trocar
> o SQLite por um banco externo (ex: Supabase/Postgres) — posso te ajudar a migrar quando
> for necessário.

## 3. Importar a lista completa de clubes do FC 26

Na aba **Clubes / Ligas > Importar arquivo**, baixe o template CSV e preencha com a lista
completa de clubes/ligas do jogo (ou use o arquivo `clubes_exemplo.csv` incluído, que já
tem uma amostra para começar a testar).

Formato esperado:
```csv
club,league
Real Madrid,La Liga
Flamengo,Brasileirão
```

## 4. Estrutura do projeto

```
app.py       -> interface Streamlit (páginas: Nova Partida, Histórico, Ranking, Jogadores, Clubes/Ligas)
db.py        -> camada de acesso ao banco SQLite
stats.py     -> cálculo de resultado, saldo de gols e ranking
clubes_exemplo.csv -> lista de exemplo para importação
requirements.txt   -> dependências
```

## 5. Modelo de dados (resumo)

- **players**: jogadores do grupo
- **clubs**: clubes vinculados a uma liga
- **matches**: uma partida (data + observação)
- **match_entries**: cada linha é "jogador X, com clube Y, no lado casa/fora, fez N gols"
  em uma partida específica — permite tanto 1x1 quanto 2x2 (múltiplos jogadores por lado).

O resultado (V/D/E) e o saldo de gols de cada jogador são sempre calculados a partir do
placar agregado do lado (casa vs. fora), não precisam ser digitados manualmente.
