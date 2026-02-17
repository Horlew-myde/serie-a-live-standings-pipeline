import streamlit as st
import pandas as pd
import requests
import os
# from dotenv import load_dotenv

# Load .env for local development (ignored in GitHub)
# load_dotenv()

# Get API credentials - works locally with .env OR on Streamlit with st.secrets
API_KEY = st.secrets.get("API_KEY")
if not API_KEY and "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]

API_HOST = "livescore6.p.rapidapi.com"  # Hardcoded (no need for .env)

@st.cache_data(ttl=86400)  # Cache for 1 hour (fetches fresh data hourly, but you can adjust)
def get_serie_a_standings():
    """Fetch and process Serie A standings from the API"""
    url = "https://livescore6.p.rapidapi.com/leagues/v2/get-table"
    
    querystring = {
        "Category": "soccer",
        "Ccd": "italy",
        "Scd": "serie-a"
    }
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()  # Raise error if API fails
    
    payload = response.json()
    
    # Extract the main league table (home/away combined)
    standing_list = payload['LeagueTable']['L'][0]['Tables'][0]['team']
    
    # Build rows for DataFrame
    rows = []
    for club in standing_list:
        season = 2025  # Hardcoded for current season (update if needed)
        position = club["rnk"]
        team = club["Tnm"]
        played = club["pld"]
        won = club["win"]
        draw = club["drw"]
        lost = club["lst"]
        goals_for = club["gf"]
        goals_against = club["ga"]
        goals_difference = club["gd"]
        points = club["pts"]
        
        rows.append((
            season, position, team, played, won, draw, lost,
            goals_for, goals_against, goals_difference, points
        ))
    
    column_names = [
        'season', 'position', 'team', 'played', 'won', 'draw', 'lost',
        'goals_for', 'goals_against', 'goals_difference', 'points'
    ]
    
    df = pd.DataFrame(rows, columns=column_names)
    return df

# ====================== STREAMLIT UI ======================
st.set_page_config(page_title="Serie A Standings", page_icon="⚽", layout="wide")

st.title("🇮🇹 Serie A League Table")
st.markdown("**Live standings fetched from RapidAPI • Updated on every refresh**")

# Fetch data
try:
    df = get_serie_a_standings()
    
    # Sort by position (just in case)
    df = df.sort_values(by='position')
    
    # Display as nice table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "position": st.column_config.NumberColumn("Pos", format="%d"),
            "team": st.column_config.TextColumn("Team"),
            "played": st.column_config.NumberColumn("P", format="%d"),
            "won": st.column_config.NumberColumn("W", format="%d"),
            "draw": st.column_config.NumberColumn("D", format="%d"),
            "lost": st.column_config.NumberColumn("L", format="%d"),
            "goals_for": st.column_config.NumberColumn("GF", format="%d"),
            "goals_against": st.column_config.NumberColumn("GA", format="%d"),
            "goals_difference": st.column_config.NumberColumn("GD", format="%d"),
            "points": st.column_config.NumberColumn("Pts", format="%d"),
        }
    )
    
    # Optional: Highlight top teams
    st.markdown("### Top 4 (Champions League spots)")
    st.dataframe(df.head(4)[['position', 'team', 'points']], use_container_width=True)
    
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.info("Make sure your API_KEY is set correctly.")

# Footer

st.caption("Built with ❤️ using Streamlit + RapidAPI • Data refreshes automatically")
