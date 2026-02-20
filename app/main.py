import os
import sys
import logging
import httpx  # Async HTTP client for better performance
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# --- 1. SYSTEM INITIALIZATION ---
# Ensures our modules in /src and /pipeline are discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importing the core logic you built in the src/pipeline folders
from pipeline.pipeline import AnimeRecommendationPipeline

# Load environment variables (Groq API Keys, etc.)
load_dotenv()

# Setup Professional Logging for production monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 2. PIPELINE LIFECYCLE MANAGEMENT ---
# We load the heavy AI models ONCE on startup using the lifespan pattern
pipeline_instance = None

async def lifespan(app: FastAPI):
    global pipeline_instance
    logger.info("🚀 Initializing AI Recommendation Pipeline...")
    try:
        pipeline_instance = AnimeRecommendationPipeline()
        logger.info("✅ Pipeline loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load pipeline: {e}")
    yield
    logger.info("🛑 Shutting down AI Engine...")

# Initialize FastAPI with the Lifespan handler
app = FastAPI(lifespan=lifespan)

# --- 3. STATIC FILES & TEMPLATES ---
# Connecting your folders to the API
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- 4. WEB INTERFACE ROUTE ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main frontend page."""
    return templates.TemplateResponse("index.html", {"request": request})

# --- 5. CORE API ENDPOINTS ---

@app.get("/api/recommend")
async def get_recommendation(query: str):
    """
    Main AI endpoint. Communicates with /src/ logic.
    Returns dynamic 5-8 recommendations with sync'd explanations.
    """
    if not pipeline_instance:
        raise HTTPException(status_code=503, detail="AI Engine is offline.")

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # Trigger the core logic in src/recommender.py via the pipeline
        raw_out = pipeline_instance.recommend(query)
        
        # Robust Parsing: Splitting titles and explanations using '|||'
        parts = raw_out.split('\n', 1)
        if len(parts) < 2:
            raise ValueError("Pipeline returned malformed output format.")

        title_line = parts[0]
        analysis_body = parts[1]

        titles = [t.strip() for t in title_line.split(',') if t.strip()]
        explanations = [e.strip() for e in analysis_body.split('|||') if e.strip()]

        # Structural Validation: Ensure data is perfectly paired for the UI
        min_count = min(len(titles), len(explanations))
        
        return {
            "success": True,
            "titles": titles[:min_count], 
            "explanations": explanations[:min_count],
            "count": min_count
        }

    except Exception as e:
        logger.error(f"Inference Error: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": "Internal AI Logic Error."}
        )

@app.get("/api/metadata")
async def get_metadata(title: str):
    """
    Fetches poster images and scores from Jikan API.
    Used for the 'Personalized Matches' grid.
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.jikan.moe/v4/anime?q={title}&limit=1"
            res = await client.get(url, timeout=10.0)
            data = res.json()
            if 'data' in data and len(data['data']) > 0:
                anime = data['data'][0]
                return {
                    "image": anime['images']['jpg']['large_image_url'],
                    "score": anime.get('score', 'N/A'),
                    "url": anime['url'],
                    "title": anime['title_english'] or anime['title']
                }
            return {"error": "Not found"}
        except Exception as e:
            return {"error": str(e)}

@app.get("/api/top-anime")
async def get_top_anime():
    """
    Fetches the live Top 50 global rankings.
    Triggered by the 'More >' link in the Trending section.
    """
    async with httpx.AsyncClient() as client:
        try:
            all_anime = []
            # Fetching two pages to get a full Top 50
            for page in [1, 2]:
                url = f"https://api.jikan.moe/v4/top/anime?page={page}"
                res = await client.get(url, timeout=10.0)
                page_data = res.json()
                if 'data' in page_data:
                    all_anime.extend(page_data['data'])
            final_data = sorted(all_anime, key=lambda x: x['rank'])[:50]
            return {
                "success": True, 
                "data": [
                    {
                        "rank": i + 1,
                        "title": a['title_english'] or a['title'],
                        "score": a['score']
                    } for i, a in enumerate(all_anime[:50])
                ]
            }
        except Exception as e:
            return JSONResponse(
                status_code=500, 
                content={"success": False, "error": f"Jikan API Error: {str(e)}"}
            )
@app.get("/api/top-characters")
async def get_top_characters():
    """
    Fetches the top 50 most popular anime characters from the live Jikan API.
    """
    async with httpx.AsyncClient() as client:
        try:
            all_chars = []
            # Jikan returns 25 per page; fetch two pages
            for page in [1, 2]:
                url = f"https://api.jikan.moe/v4/top/characters?page={page}"
                res = await client.get(url, timeout=10.0)
                page_data = res.json()
                if 'data' in page_data:
                    all_chars.extend(page_data['data'])
            
            # Slice to exactly 50 and return clean data
            return {
                "success": True, 
                "data": [
                    {
                        "rank": i + 1,
                        "name": c['name'],
                        "anime": c['about'] if 'about' in c else "N/A" # or c['anime'][0]['anime']['title']
                    } for i, c in enumerate(all_chars[:50])
                ]
            }
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

# --- 6. EXECUTION BLOCK ---
if __name__ == "__main__":
    import uvicorn
    # In production/deployment, uvicorn will be called via the Dockerfile command.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)