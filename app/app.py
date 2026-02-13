import sys
import os
import requests
import streamlit as st
from dotenv import load_dotenv

# --- SYSTEM INITIALIZATION ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Defensive Import Pattern for Production
try:
    from pipeline.pipeline import AnimeRecommendationPipeline
    PIPELINE_AVAILABLE = True
except Exception as e:
    st.error(f"Critical System Failure: Could not load Recommendation Pipeline. {e}")
    PIPELINE_AVAILABLE = False

# ... [Other code] ...

@st.cache_resource
def init_pipeline():
    if not PIPELINE_AVAILABLE:
        st.stop() # Prevents NameError by halting execution gracefully
    return AnimeRecommendationPipeline()


# --- 1. PAGE ARCHITECTURE ---
st.set_page_config(
    page_title="AI Anime Explorer | Premium Edition",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="collapsed"
)
# --- CRITICAL FIX: SESSION STATE INITIALIZATION ---
if 'active_page' not in st.session_state:
    st.session_state.active_page = "home" # Default landing page

# --- 2. MASTER UI ENGINE (CSS) ---
# Implements Parallax, Glassmorphism, and the specific Search Bar geometry.
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Montserrat:wght@900&display=swap');

    /* --- GLOBAL THEME --- */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
    }

    /* Hide Default UI Clutter */
    [data-testid="stSidebar"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* --- VIBRANT PARALLAX BACKGROUND --- */
    .stApp {
        background-image: linear-gradient(rgba(139, 0, 0, 0.5), rgba(0, 0, 0, 0.8)),
                          url("https://images.unsplash.com/photo-1541562232579-512a21360020?q=80&w=2000&auto=format&fit=crop");
        background-size: cover;
        background-position: center top;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    /* --- GLASSMORPHISM PANEL --- */
    .main .block-container {
        background: rgba(20, 20, 20, 0.85);
        backdrop-filter: blur(20px);
        border-radius: 30px;
        padding: 60px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.9);
        margin-top: 40px;
    }

    /* --- TITLES --- */
    .main-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        letter-spacing: -2px;
    }

    .sub-title {
        text-align: center;
        color: #d1d5db;
        font-size: 1.4rem;
        margin-bottom: 60px;
        font-weight: 300;
    }

    /* --- NAVIGATION DOCK --- */
    .stButton > button {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        border: none;
        color: white;
        padding: 18px 25px;
        border-radius: 50px;
        transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        font-weight: 700;
        width: 100%;
        box-shadow: 0 10px 20px rgba(0, 198, 255, 0.4);
        text-transform: capitalize;
    }
    .stButton > button:hover {
        transform: scale(1.05) translateY(-5px);
        box-shadow: 0 15px 30px rgba(0, 198, 255, 0.6);
    }

    /* --- REDESIGNED SEARCH BAR --- */
    /* Constrained width, high verticality, and rounded corners */
    [data-testid="stTextInput"] {
        max-width: 850px !important;
        margin: 0 auto !important;
    }

    .stTextInput > div > div > input {
        height: 75px !important;
        border-radius: 40px !important;
        padding: 0 35px !important;
        font-size: 1.2rem !important;
        border: 2px solid rgba(0, 198, 255, 0.3) !important;
        background-color: rgba(0, 0, 0, 0.4) !important;
        color: #ffffff !important;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #00c6ff !important;
        box-shadow: 0 0 25px rgba(0, 198, 255, 0.5) !important;
    }

    /* --- TRENDING CARDS --- */
    .mal-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 30px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 30px;
    }
    .card-header {
        font-size: 1.5rem;
        font-weight: 800;
        border-bottom: 3px solid #00c6ff;
        padding-bottom: 12px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
    }
    .list-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    .rank-val { color: #00c6ff; font-weight: 900; margin-right: 15px; font-size: 1.3rem; }

    /* --- RESULT BOX --- */
    .reasoning-box {
        background: rgba(0, 198, 255, 0.05);
        padding: 30px;
        border-radius: 20px;
        border-left: 8px solid #00c6ff;
        line-height: 1.9;
        font-size: 1.15rem;
        color: #e2e8f0;
        margin-top: 40px;
    }
    
    /* --- ENHANCED RECOMMENDATION ITEMS --- */
    .rec-item-container {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid rgba(0, 198, 255, 0.1);
        transition: transform 0.3s ease;
    }
    .rec-item-container:hover {
        background: rgba(0, 198, 255, 0.05);
        border-color: #00c6ff;
        transform: translateX(10px);
    }
    .rec-title {
        color: #00c6ff;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .rec-label {
        color: #818cf8;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 1px;
    }
    .rec-text {
        color: #e2e8f0;
        line-height: 1.7;
        margin-bottom: 15px;
    }
    /* --- PRODUCTION-GRADE RESULT CARDS --- */
    .rec-item-container {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 18px;
        padding: 30px;
        margin-bottom: 25px;
        border: 1px solid rgba(0, 198, 255, 0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .rec-item-container:hover {
        border-color: #00c6ff;
        transform: translateY(-5px);
        background: rgba(0, 198, 255, 0.06);
    }
    .rec-label {
        color: #00c6ff;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BACKEND UTILITIES ---
load_dotenv()

@st.cache_resource
def init_pipeline():
    return AnimeRecommendationPipeline()

@st.cache_data(ttl=3600)
def fetch_api_data(title):
    try:
        url = f"https://api.jikan.moe/v4/anime?q={title}&limit=1"
        res = requests.get(url, timeout=10).json()
        if 'data' in res and len(res['data']) > 0:
            anime = res['data'][0]
            return {
                "image": anime['images']['jpg']['large_image_url'],
                "score": anime.get('score', 'N/A'),
                "url": anime['url'],
                "title": anime['title_english'] or anime['title']
            }
    except Exception:
        return None

# --- UPDATED RECOMMENDATION ROUTE ---
if st.session_state.active_page == "recommend":
    pipeline = init_pipeline()
    user_query = st.text_input("", placeholder="Enter your vibe (e.g., 'Dark psychological thriller like Death Note')...")

    if user_query:
        with st.status("✨ Shifting through the archives...", expanded=True) as status:
            # Generate response
            raw_out = pipeline.recommend(user_query)
            status.update(label="✅ Matches Found!", state="complete", expanded=False)
            
            # ROBUST PARSING ENGINE
            try:
                parts = raw_out.split('\n', 1)
                title_line = parts[0]
                titles = [t.strip() for t in title_line.split(',')]
                
                analysis_body = parts[1] if len(parts) > 1 else ""
                explanations = [e.strip() for e in analysis_body.split('|||') if e.strip()]
                
                st.divider()
                st.markdown("## ✨ Personalized Matches")
                
                # Render Poster Grid
                res_grid = st.columns(3)
                for i, title in enumerate(titles[:3]):
                    meta = fetch_api_data(title)
                    with res_grid[i]:
                        if meta:
                            st.image(meta['image'], use_container_width=True)
                            st.markdown(f"#### {meta['title']}")
                            st.markdown(f"**⭐ Score: {meta['score']}**")
                            st.link_button("View on MAL", meta['url'], use_container_width=True)

                # STREAMING NARRATIVE CONNECTION
                st.markdown("### 📝 The Narrative Connection")
                for exp in explanations:
                    with st.container():
                        st.markdown('<div class="rec-item-container">', unsafe_allow_html=True)
                        # Types the explanation out chunk by chunk
                        st.write_stream(iter(exp.split(' '))) 
                        st.markdown('</div>', unsafe_allow_html=True)
            
            except Exception as e:
                st.error("The Connoisseur is having trouble describing these. Please try a different vibe!")
                st.debug(f"Parsing error: {e}")

# --- 4. HEADER & NAV DOCK ---
st.markdown("<h1 class='main-title'>AI Anime Explorer</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Crafting your unique journey through the world of anime</p>", unsafe_allow_html=True)

nav_c1, nav_c2, nav_c3, nav_c4, nav_c5 = st.columns(5)

with nav_c1: 
    if st.button("🖼️ Generate Poster"):
        st.session_state.active_page = "poster"
with nav_c2: 
    if st.button("✨ Recommend"):
        st.session_state.active_page = "recommend"
with nav_c3: 
    if st.button("📑 My Watchlist"):
        st.session_state.active_page = "watchlist"
with nav_c4: 
    if st.button("📺 Watch Anime"):
        st.session_state.active_page = "watch"
with nav_c5: 
    if st.button("🛒 Shopping"):
        st.session_state.active_page = "shop"

# --- 5. PAGE ROUTING & CONTENT ---

# ROUTE: RECOMMENDATION PAGE (Primary RAG Interface)
if st.session_state.active_page == "recommend":
    pipeline = init_pipeline()
    user_query = st.text_input("", placeholder="Describe your vibe (e.g., 'A rainy day in a futuristic Tokyo')")

    if user_query:
        # Using st.status for better observability of the background process
        with st.status("🔍 Analyzing Vibe & Querying Vector DB...", expanded=True) as status:
            raw_out = pipeline.recommend(user_query)
            
            # STAGE 1: Data Normalization & Robust Parsing
            try:
                # Splitting the initial title line from the analytical body
                parts = raw_out.split('\n', 1)
                title_line = parts[0]
                
                # Handling the body split using the Master Delimiter '|||'
                # We filter out empty strings to prevent rendering empty cards
                analysis_body = parts[1] if len(parts) > 1 else ""
                titles = [t.strip() for t in title_line.split(',')]
                explanations = [e.strip() for e in analysis_body.split('|||') if e.strip()]
                
                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

                st.divider()
                st.markdown("## ✨ Personalized Matches")
                
                # --- Poster Grid (Visual Identification) ---
                res_grid = st.columns(3)
                for i, title in enumerate(titles[:3]):
                    meta = fetch_api_data(title)
                    with res_grid[i]:
                        if meta:
                            st.image(meta['image'], use_container_width=True)
                            st.markdown(f"#### {meta['title']}")
                            st.markdown(f"**⭐ Score: {meta['score']}**")
                            st.link_button("View on MAL", meta['url'], use_container_width=True)
                        else:
                            st.info(f"Details for '{title}' not found.")

                # --- Enhanced Separation Rendering (Narrative Analysis) ---
                st.markdown("### 📝 Detailed Narrative Connection")
                for idx, exp in enumerate(explanations):
                    # Each explanation is isolated in its own CSS container for clear distinction
                    st.markdown(f"""
                    <div class="rec-item-container">
                        <div class="rec-label">Match Rank #{idx + 1}</div>
                        <div class="rec-text">{exp}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            except Exception as e:
                status.update(label="❌ Engine Error", state="error")
                st.error(f"The Connoisseur is having trouble parsing this vibe. Error: {str(e)}")

# --- SECONDARY ROUTES (Placeholders for Expansion) ---

elif st.session_state.active_page == "poster":
    st.markdown("## 🖼️ Anime Poster Generator")
    st.info("The Stable Diffusion API is being integrated for custom artwork generation.")

elif st.session_state.active_page == "watchlist":
    st.markdown("## 📑 Your Personal Watchlist")
    st.info("Database synchronization in progress. This feature will use SQLite for persistence.")

elif st.session_state.active_page == "watch":
    st.markdown("## 📺 Stream Anime")
    st.info("Searching for secure streaming providers... Feature integration in progress.")

elif st.session_state.active_page == "shop":
    st.markdown("## 🛒 Anime Merchandise Store")
    st.info("The marketplace is currently under maintenance. Check back later!")

# ROUTE: HOME (Default Clean Landing Page)
else:
    # Landing page is handled by the always-visible Trending section (Section 6)
    pass
    
# --- 6. TRENDING & FOOTER (MAL STYLE) ---
st.markdown("<br><br><h2>🔥 Trending Now</h2>", unsafe_allow_html=True)
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("""
    <div class="mal-card">
        <div class="card-header">Top Anime <span style="font-size: 0.9rem; color: #94a3b8;">More ></span></div>
        <div class="list-item"><span class="rank-val">1</span> Frieren: Beyond Journey's End</div>
        <div class="list-item"><span class="rank-val">2</span> Fullmetal Alchemist: Brotherhood</div>
        <div class="list-item"><span class="rank-val">3</span> Steins;Gate</div>
        <div class="list-item"><span class="rank-val">4</span> Gintama°</div>
    </div>
    """, unsafe_allow_html=True)

with col_r:
    st.markdown("""
    <div class="mal-card">
        <div class="card-header">Popular Characters <span style="font-size: 0.9rem; color: #94a3b8;">More ></span></div>
        <div class="list-item"><span class="rank-val">1</span> Lelouch Lamperouge (Code Geass)</div>
        <div class="list-item"><span class="rank-val">2</span> Levi Ackerman (Attack on Titan)</div>
        <div class="list-item"><span class="rank-val">3</span> Monkey D. Luffy (One Piece)</div>
        <div class="list-item"><span class="rank-val">4</span> L Lawliet (Death Note)</div>
    </div>
    """, unsafe_allow_html=True)

# --- 7. FOOTER ---
st.markdown("""
    <div style="text-align: center; padding-top: 80px; color: #94a3b8; font-size: 0.9rem; padding-bottom: 40px;">
        <hr style="border: 0.5px solid rgba(255,255,255,0.1)">
        Built with ❤️ by Rohit Parida | 6th Sem CSE Portfolio Project<br>
        Powered by Groq & ChromaDB. Real-time data via Jikan API.
    </div>
""", unsafe_allow_html=True)