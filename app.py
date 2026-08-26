import os
import requests
import pandas as pd
import streamlit as st

# -----------------------------
# Configuration & Setup
# -----------------------------
st.set_page_config(
    page_title="Serie A Dashboard",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# RapidAPI Credentials
API_KEY = "ea792a59a3msh0e2da56cee146d3p17f2f7jsn76e3483ef0b1"
API_HOST = "free-api-live-football-data.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
    "Content-Type": "application/json"
}

# Strictly Serie A
LEAGUE_ID = 55
SEASON = "Current"

# -----------------------------
# Data Fetching Functions
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
        column_names = ['season', 'position', 'team', 'played', 'won', 'draw', 'lost', 'goals_for', 'goals_against', 'goals_difference', 'points']
        
        for club in standings_list:
            season_val = season
            position = club.get("idx")
            team = club.get("name")
            played = club.get("played")
            won = club.get("wins")
            draw = club.get("draws")
            lost = club.get("losses")
            
            scores_str = club.get("scoresStr", "0-0")
            if "-" in scores_str:
                scores = scores_str.split("-")
                goals_for = int(scores[0])
                goals_against = int(scores[1])
            else:
                goals_for = 0
                goals_against = 0
                
            goals_difference = club.get("goalConDiff")
            points = club.get("pts")
            
            tuple_of_club_records = (season_val, position, team, played, won, draw, lost, goals_for, goals_against, goals_difference, points)
            rows.append(tuple_of_club_records)
            
        return pd.DataFrame(rows, columns=column_names)
    except Exception as e:
        st.error(f"Error fetching standings: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_player_stats(endpoint_name: str, league_id: int) -> pd.DataFrame:
    """Fetch player stats and parse into a DataFrame."""
    url = f"https://free-api-live-football-data.p.rapidapi.com/{endpoint_name}"
    params = {"leagueid": str(league_id)}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        raw_response = data.get("response", [])
        player_list = []
        
        if isinstance(raw_response, list):
            player_list = raw_response
        elif isinstance(raw_response, dict):
            # Locate the list inside the dictionary
            for key, val in raw_response.items():
                if isinstance(val, list):
                    player_list = val
                    break
                    
        rows = []
        if player_list:
            for player in player_list:
                player_name = player.get("name", "N/A")
                
                # Determine stat type dynamically
                if "goals" in player:
                    stat_val, stat_name = player.get("goals"), "Goals"
                elif "assists" in player:
                    stat_val, stat_name = player.get("assists"), "Assists"
                elif "rating" in player:
                    stat_val, stat_name = player.get("rating"), "Rating"
                else:
                    stat_val = next((v for k, v in player.items() if isinstance(v, (int, float)) and k != "id"), "N/A")
                    stat_name = "Value"
                
                # FIX: Removed the undefined 'position' variable here
                rows.append((player_name, stat_val))
                
            return pd.DataFrame(rows, columns=["Player", stat_name])
            
        return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"Error fetching {endpoint_name}: {e}")
        return pd.DataFrame()

# -----------------------------
# Load Data
# -----------------------------
standings_df = fetch_standings(LEAGUE_ID)
top_goals_df = fetch_player_stats("football-get-top-players-by-goals", LEAGUE_ID)
top_assists_df = fetch_player_stats("football-get-top-players-by-assists", LEAGUE_ID)
top_ratings_df = fetch_player_stats("football-get-top-players-by-rating", LEAGUE_ID)

# -----------------------------
# Main Content Area: Standings
# -----------------------------
st.title("🏆 Serie A (Italy) Dashboard")

if not standings_df.empty:
    st.dataframe(
        standings_df.set_index("position"), 
        use_container_width=True, 
        height=800
    )
else:
    st.warning("No league standings data available right now.")

# -----------------------------
# Sidebar Area: Player Statistics
# -----------------------------
st.sidebar.title("📊 Player Statistics")

st.sidebar.markdown("### ⚽ Top Goalscorers")
if not top_goals_df.empty:
    top_goals_df.index = top_goals_df.index + 1
    st.sidebar.dataframe(top_goals_df, use_container_width=True)

st.sidebar.markdown("### 🎯 Top Assists")
if not top_assists_df.empty:
    top_assists_df.index = top_assists_df.index + 1
    st.sidebar.dataframe(top_assists_df, use_container_width=True)

st.sidebar.markdown("### ⭐ Player Ratings")
if not top_ratings_df.empty:
    top_ratings_df.index = top_ratings_df.index + 1
    st.sidebar.dataframe(top_ratings_df, use_container_width=True)
