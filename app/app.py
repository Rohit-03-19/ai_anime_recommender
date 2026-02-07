import sys
import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Force Python to look at the main project folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.pipeline import AnimeRecommendationPipeline

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Anime Explorer", layout="wide", page_icon="🎬")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background-color: #6366f1; color: white; border-radius: 5px; width: 100%;
    }
    .recommendation-box {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #6366f1;
        margin-top: 20px;
    }
    .rating-text { color: #facc15; font-weight: bold; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

@st.cache_resource
def init_pipeline():
    return AnimeRecommendationPipeline()

def fetch_metadata(title):
    """Fetches real-time posters and ratings from Jikan API."""
    try:
        url = f"https://api.jikan.moe/v4/anime?q={title}&limit=1"
        res = requests.get(url).json()
        if 'data' in res and len(res['data']) > 0:
            anime = res['data'][0]
            return {
                "image": anime['images']['jpg']['large_image_url'],
                "score": anime.get('score', 'N/A'),
                "url": anime['url'],
                "title": anime['title_english'] or anime['title']
            }
    except:
        return None

# --- MAIN APP INTERFACE ---
st.title("🎬 AI Anime Recommender")
st.markdown("### *Discover your next favorite anime using Semantic Search*")

pipeline = init_pipeline()

query = st.text_input("", placeholder="Tell me about the themes or vibes you enjoy...")

if query:
    with st.spinner("🧠 Analyzing database..."):
        # 1. Get raw response
        raw_response = pipeline.recommend(query)
        
        # 2. Parse response (Titles on line 1, descriptions after)
        parts = raw_response.split('\n', 1)
        
        if len(parts) >= 1:
            title_line = parts[0]
            detailed_analysis = parts[1] if len(parts) > 1 else ""
            
            recommended_titles = [t.strip() for t in title_line.split(',')]
            
            st.divider()
            st.subheader("✨ Personalized Matches")
            
            # 3. Display Poster Grid
            cols = st.columns(3)
            for i, title in enumerate(recommended_titles[:3]):
                data = fetch_metadata(title)
                with cols[i]:
                    if data:
                        st.image(data['image'], use_container_width=True)
                        st.markdown(f"**{data['title']}**")
                        st.markdown(f"<span class='rating-text'>⭐ {data['score']}</span>", unsafe_allow_html=True)
                        st.link_button("Details", data['url'])
                    else:
                        st.info(f"'{title}'")
            
            # 4. Display Analysis
            st.markdown("### 📝 Why these were chosen")
            st.markdown(f'<div class="recommendation-box">{detailed_analysis}</div>', unsafe_allow_html=True)
        else:
            st.error("Unexpected response format. Please try a different query.")

# --- SIDEBAR ---
with st.sidebar:
    st.title("Project Details")
    st.write("**Developed by:** Rohit")
    st.write("**Tech:** RAG Pipeline (ChromaDB + Groq)")
    st.divider()
    if st.button("Reset App"):
        st.cache_resource.clear()
        st.rerun()