import streamlit as st
import pandas as pd
import requests

# ============================================================
# CONFIG
# ============================================================
# NOTE: your standings-building notebook used the
# "free-api-live-football-data" RapidAPI product (endpoints named
# like "football-get-standing-all", "football-get-top-players-by-goals"),
# while your deployed main.py was calling a DIFFERENT API ("livescore6")
# that doesn't have those player-stat endpoints at all — that mismatch
# is why the goalscorer/assist/rating calls were failing.
# This version uses ONE consistent API for everything.

API_KEY = st.secrets.get("API_KEY")
API_HOST = "free-api-live-football-data.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}"

LEAGUE_ID = 55          # Serie A
SEASON = "Current"
SEASON_LABEL = "2026 / 2027"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
}

TEAM_COLORS = {
    "Roma": "#8B0000", "Inter": "#0068A8", "Lecce": "#FFDD00", "Napoli": "#087C90",
    "Milan": "#FB090B", "Atalanta": "#1E71B8", "Cagliari": "#A2231D", "Juventus": "#000000",
    "Lazio": "#87D8F7", "Como": "#00539F", "Udinese": "#000000", "Sassuolo": "#00A650",
    "Torino": "#8B1F2B", "Bologna": "#8B0000", "Frosinone": "#FFCC00", "Parma": "#FFCC00",
    "Genoa": "#B0281A", "Venezia": "#FF8000", "Monza": "#FF0000", "Fiorentina": "#5B2A86",
}


# ============================================================
# DATA FETCHING (each one isolated so a single bad call
# can't take down the rest of the app)
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_standings():
    url = f"{BASE_URL}/football-get-standing-all"
    params = {"leagueid": LEAGUE_ID, "season": SEASON}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    standing_list = payload["response"]["standing"]

    rows = []
    for club in standing_list:
        rank = club.get("idx")
        team = club.get("name")
        played = club.get("played", 0)
        won = club.get("wins", 0)
        draw = club.get("draws", 0)
        lost = club.get("losses", 0)

        scores = club.get("scoresStr", "0-0").split("-")
        goals_for = int(scores[0]) if len(scores) == 2 else 0
        goals_against = int(scores[1]) if len(scores) == 2 else 0
        goal_diff = club.get("goalConDiff", goals_for - goals_against)
        points = club.get("pts", 0)

        rows.append((rank, team, played, won, draw, lost, goals_for, goals_against, goal_diff, points))

    df = pd.DataFrame(
        rows,
        columns=["position", "team", "played", "won", "draw", "lost",
                 "goals_for", "goals_against", "goal_diff", "points"],
    )
    return df.sort_values("position").reset_index(drop=True), payload


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_top_players(stat: str):
    """
    stat: 'goals' | 'assists' | 'rating'
    Returns (dataframe, raw_payload)
    """
    endpoint = f"football-get-top-players-by-{stat}"
    url = f"{BASE_URL}/{endpoint}"
    params = {"leagueid": LEAGUE_ID, "season": SEASON}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    # The exact key the list sits under can vary by endpoint, so we
    # check the common possibilities instead of assuming one shape.
    container = payload.get("response", payload.get("data", payload))
    players_raw = None
    if isinstance(container, list):
        players_raw = container
    elif isinstance(container, dict):
        for key in ("players", "topPlayers", "topplayers", "playerStats",
                    "list", "topScorers", "topscorers", "ranking"):
            if key in container and isinstance(container[key], list):
                players_raw = container[key]
                break

    if players_raw is None:
        raise ValueError(
            "Couldn't find a player list in the API response. "
            "Expand 'raw response' below to see the actual shape and "
            "adjust the key lookup in fetch_top_players()."
        )

    rows = []
    for i, entry in enumerate(players_raw, start=1):
        player_info = entry.get("player", entry)
        team_info = entry.get("team", {})

        name = player_info.get("name") or player_info.get("Pname") or "Unknown"
        team = team_info.get("name") or entry.get("teamName") or "-"

        value = (
            entry.get(stat)
            or entry.get(stat.rstrip("s"))
            or entry.get("value")
            or 0
        )
        appearances = entry.get("played") or entry.get("appearances") or "-"

        rows.append((i, name, team, value, appearances))

    df = pd.DataFrame(rows, columns=["rank", "player", "team", stat, "played"])
    return df, payload


# ============================================================
# STYLING
# ============================================================
st.set_page_config(page_title="Serie A Dashboard", page_icon="🏆", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }

.hero {
    background: linear-gradient(135deg, #0B3D91 0%, #1E71B8 45%, #00A651 100%);
    padding: 2.2rem 2rem;
    border-radius: 18px;
    margin-bottom: 1.6rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
.hero h1 {
    color: white;
    font-size: 2.1rem;
    font-weight: 800;
    margin: 0;
}
.hero p {
    color: rgba(255,255,255,0.85);
    margin-top: 0.4rem;
    font-size: 1rem;
}

.zone-card {
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    background: rgba(255,255,255,0.03);
    border-left: 5px solid #444;
}
.zone-cl { border-left-color: #00A651; }
.zone-rel { border-left-color: #E63946; }

table.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
    border-radius: 12px;
    overflow: hidden;
}
table.styled-table thead tr {
    background: rgba(255,255,255,0.06);
    text-align: left;
}
table.styled-table th, table.styled-table td {
    padding: 0.55rem 0.8rem;
}
table.styled-table tbody tr {
    border-bottom: 1px solid rgba(255,255,255,0.06);
    transition: background 0.15s ease-in-out;
}
table.styled-table tbody tr:hover {
    background: rgba(255,255,255,0.06);
}
.pos-badge {
    display: inline-block;
    min-width: 22px;
    text-align: center;
    border-radius: 6px;
    padding: 2px 6px;
    font-weight: 700;
    font-size: 0.8rem;
}
.pos-cl { background: rgba(0,166,81,0.2); color: #4CD97B; }
.pos-rel { background: rgba(230,57,70,0.2); color: #FF7B85; }
.pos-mid { background: rgba(255,255,255,0.08); color: #ccc; }

.player-card {
    background: rgba(255,255,255,0.04);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(255,255,255,0.05);
}
.player-rank {
    font-size: 1.1rem;
    font-weight: 800;
    width: 34px;
}
.player-name { font-weight: 700; font-size: 1rem; }
.player-team { font-size: 0.8rem; color: #999; }
.player-value {
    font-size: 1.3rem;
    font-weight: 800;
    color: #4CD97B;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS FOR RENDERING
# ============================================================
def pos_badge(pos: int) -> str:
    if pos <= 4:
        cls = "pos-cl"
    elif pos >= 18:
        cls = "pos-rel"
    else:
        cls = "pos-mid"
    return f'<span class="pos-badge {cls}">{pos}</span>'


def render_standings_table(df: pd.DataFrame):
    header = """
    <tr>
        <th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th>
        <th>GF</th><th>GA</th><th>GD</th><th>Pts</th>
    </tr>
    """
    body_rows = []
    for _, r in df.iterrows():
        dot_color = TEAM_COLORS.get(r["team"], "#888")
        body_rows.append(f"""
        <tr>
            <td>{pos_badge(int(r['position']))}</td>
            <td><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
                background:{dot_color};margin-right:8px;"></span>{r['team']}</td>
            <td>{r['played']}</td>
            <td>{r['won']}</td>
            <td>{r['draw']}</td>
            <td>{r['lost']}</td>
            <td>{r['goals_for']}</td>
            <td>{r['goals_against']}</td>
            <td>{r['goal_diff']}</td>
            <td><b>{r['points']}</b></td>
        </tr>
        """)
    html = f"""
    <table class="styled-table">
        <thead>{header}</thead>
        <tbody>{''.join(body_rows)}</tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_leaderboard(df: pd.DataFrame, stat: str, medal_emojis=("🥇", "🥈", "🥉")):
    for _, r in df.iterrows():
        rank = int(r["rank"])
        medal = medal_emojis[rank - 1] if rank <= 3 else f"#{rank}"
        st.markdown(f"""
        <div class="player-card">
            <div style="display:flex;align-items:center;gap:1rem;">
                <div class="player-rank">{medal}</div>
                <div>
                    <div class="player-name">{r['player']}</div>
                    <div class="player-team">{r['team']} · {r['played']} apps</div>
                </div>
            </div>
            <div class="player-value">{r[stat]}</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div class="hero">
    <h1>🇮🇹 Serie A Dashboard</h1>
    <p>Live standings & player stats · Season {SEASON_LABEL} · Refreshes hourly</p>
</div>
""", unsafe_allow_html=True)

if not API_KEY:
    st.error("No API_KEY found in Streamlit secrets. Add it under Settings → Secrets.")
    st.stop()

tab_standings, tab_goals, tab_assists, tab_ratings = st.tabs(
    ["🏆 Standings", "⚽ Top Scorers", "🎯 Top Assists", "⭐ Player Ratings"]
)

# ------------------------------------------------------------
# TAB 1 — STANDINGS
# ------------------------------------------------------------
with tab_standings:
    try:
        df, raw = fetch_standings()

        col1, col2, col3 = st.columns(3)
        leader = df.iloc[0]
        col1.metric("League Leader", leader["team"], f"{leader['points']} pts")
        col2.metric("Matches Played (avg)", f"{df['played'].mean():.0f}")
        col3.metric("Total Goals Scored", int(df["goals_for"].sum()))

        st.markdown("#### Full Table")
        render_standings_table(df)

        cA, cB = st.columns(2)
        with cA:
            st.markdown('<div class="zone-card zone-cl"><b>🟢 Champions League spots (Top 4)</b></div>',
                        unsafe_allow_html=True)
            render_standings_table(df.head(4))
        with cB:
            st.markdown('<div class="zone-card zone-rel"><b>🔴 Relegation zone (Bottom 3)</b></div>',
                        unsafe_allow_html=True)
            render_standings_table(df.tail(3))

        with st.expander("Raw API response (debug)"):
            st.json(raw)

    except Exception as e:
        st.error(f"Couldn't load standings: {e}")
        st.info("Double-check your API_KEY is set correctly in Streamlit secrets.")

# ------------------------------------------------------------
# TAB 2 — TOP SCORERS
# ------------------------------------------------------------
with tab_goals:
    try:
        df, raw = fetch_top_players("goals")
        st.markdown("#### Top Goalscorers")
        render_leaderboard(df.head(10), "goals")
        with st.expander("Raw API response (debug)"):
            st.json(raw)
    except Exception as e:
        st.error(f"Couldn't load top scorers: {e}")

# ------------------------------------------------------------
# TAB 3 — TOP ASSISTS
# ------------------------------------------------------------
with tab_assists:
    try:
        df, raw = fetch_top_players("assists")
        st.markdown("#### Top Assists")
        render_leaderboard(df.head(10), "assists")
        with st.expander("Raw API response (debug)"):
            st.json(raw)
    except Exception as e:
        st.error(f"Couldn't load top assists: {e}")

# ------------------------------------------------------------
# TAB 4 — PLAYER RATINGS
# ------------------------------------------------------------
with tab_ratings:
    try:
        df, raw = fetch_top_players("rating")
        st.markdown("#### Highest Rated Players")
        render_leaderboard(df.head(10), "rating")
        with st.expander("Raw API response (debug)"):
            st.json(raw)
    except Exception as e:
        st.error(f"Couldn't load player ratings: {e}")

st.caption("Built with ❤️ using Streamlit + RapidAPI · Data refreshes automatically")
