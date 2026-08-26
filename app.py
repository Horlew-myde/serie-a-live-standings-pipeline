import os
import requests
import pandas as pd
import streamlit as st

# -----------------------------
# Configuration & Page Style
# -----------------------------
st.set_page_config(
    page_title="Serie A Live Standings",
    page_icon="⚽",
    layout="wide",
)

# Custom CSS for a cleaner, centered look
st.markdown("""
    <style>
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stMetric {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# API Credentials
# -----------------------------
API_KEY = "ea792a59a3msh0e2da56cee146d3p17f2f7jsn76e3483ef0b1"
API_HOST = "free-api-live-football-data.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
    "Content-Type": "application/json"
}

LEAGUE_ID = 55
SEASON = "Current"

# -----------------------------
# Data Fetching Function
# -----------------------------
@st.cache_data(ttl=3600)
def fetch_standings(league_id: int, season: str = "Current") -> pd.DataFrame:
    """Fetch and parse league standings."""
    url = "https://free-api-live-football-data.p.rapidapi.com/football-get-standing-all"
    params = {"leagueid": league_id, "season": season}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        standings_list = data.get("response", {}).get("standing", [])
        rows = []
        column_names = ['Season', 'Pos', 'Team', 'Played', 'Won', 'Draw', 'Lost', 'GF', 'GA', 'GD', 'Points']
        
        for club in standings_list:
            scores_str = club.get("scoresStr", "0-0")
            scores = scores_str.split("-") if "-" in scores_str else [0, 0]
                
            rows.append((
                season, 
                club.get("idx"), 
                club.get("name"), 
                club.get("played"), 
                club.get("wins"), 
                club.get("draws"), 
                club.get("losses"), 
                int(scores[0]), 
                int(scores[1]), 
                club.get("goalConDiff"), 
                club.get("pts")
            ))
            
        return pd.DataFrame(rows, columns=column_names)
    except Exception as e:
        st.error(f"Error fetching standings: {e}")
        return pd.DataFrame()

# -----------------------------
# Main Content Area
# -----------------------------
st.markdown("<h1 style='text-align: center;'>🏆 Serie A Matchweek Standings</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888; font-size: 18px;'>Real-time league table updates pulled directly from live sports APIs.</p>", unsafe_allow_html=True)
st.markdown("---")

standings_df = fetch_standings(LEAGUE_ID)

if not standings_df.empty:
    # Highlight Metrics Row
    leader = standings_df.iloc[0]
    runner_up = standings_df.iloc[1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🥇 1st Place", leader["Team"], f"{leader['Points']} pts")
    col2.metric("🥈 2nd Place", runner_up["Team"], f"{runner_up['Points']} pts")
    col3.metric("⚽ Total Teams Tracked", len(standings_df))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Beautified DataFrame
    st.dataframe(
        standings_df.set_index("Pos"), 
        use_container_width=True, 
        height=750
    )
else:
    st.warning("No league standings data available right now.")
