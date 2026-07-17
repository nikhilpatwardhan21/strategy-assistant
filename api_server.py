from fastapi import FastAPI          #type:ignore
from fastapi.middleware.cors import CORSMiddleware        #type:ignore
from main import run_race_pipeline
from src.vectordb.vector_store import F1VectorStoreManager
from src.llm.llm_client import OpenAIEngine
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG components
vdb_manager = F1VectorStoreManager()
llm_client = OpenAIEngine()

# Auto-seed the vector database with F1 historical stats on startup
try:
    if vdb_manager.collection.count() == 0:
        vdb_manager.add_historical_stats()
except Exception as e:
    print(f"⚠️ Warning: Failed to auto-seed historical stats: {e}")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "F1 Strategy & Anchor RAG Engine is running!",
        "version": "2.0"
    }

@app.post("/simulate")
async def simulate(data: dict):
    # Extracts circuit and strategy from the React request
    circuit = data.get("circuit")
    strategy = data.get("strategy")
    
    # Calls your function and returns the data to React
    result = run_race_pipeline(circuit, strategy) 
    return {"data": result}

@app.post("/ingest")
async def ingest(data: dict):
    url = data.get("url")
    if not url:
        return {"status": "error", "message": "Missing URL parameter."}
    
    source_id = hashlib.md5(url.encode('utf-8')).hexdigest()[:10]
    
    try:
        success = vdb_manager.ingest_live_web_data(url, source_id)
        if success:
            return {"status": "success", "message": f"Successfully ingested and indexed data from {url}"}
        else:
            return {"status": "error", "message": "Failed to scrape text from the provided URL."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/query")
async def query(data: dict):
    question = data.get("question")
    if not question:
        return {"status": "error", "message": "Missing question parameter."}
    
    try:
        context, metadata = vdb_manager.query_similar_context(question)
        
        # Build prompt format that llm_client expects
        prompt = f"""
        [VERIFIED DATABASE CONTEXT]
        {context}
        [USER QUESTION]
        {question}
        """
        
        answer = llm_client.generate_response(prompt)
        
        # Collect unique sources
        sources = []
        for m in metadata:
            src = m.get("source_url") or m.get("source") or "unknown"
            if src not in sources:
                sources.append(src)
                
        return {
            "status": "success",
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/standings")
async def get_standings():
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get('https://www.formula1.com/en/results.html/2026/drivers.html', headers=headers, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table')
            if table:
                trs = table.find_all('tr')
                standings = []
                for tr in trs[1:]:
                    cols = [s.strip() for s in tr.strings if s.strip()]
                    if len(cols) >= 5:
                        pos = cols[0]
                        code = cols[-4]
                        nationality = cols[-3]
                        team = cols[-2]
                        pts = cols[-1]
                        name = " ".join(cols[1:-4])
                        standings.append({
                            "position": pos,
                            "name": name,
                            "code": code,
                            "nationality": nationality,
                            "team": team,
                            "points": pts
                        })
                return {"status": "success", "data": standings}
    except Exception as e:
        print(f"[WARN] Standings scraping failed: {e}")
        
    fallback_standings = [
        {"position": "1", "name": "Kimi Antonelli", "code": "ANT", "nationality": "ITA", "team": "Mercedes", "points": "179"},
        {"position": "2", "name": "George Russell", "code": "RUS", "nationality": "GBR", "team": "Mercedes", "points": "154"},
        {"position": "3", "name": "Lewis Hamilton", "code": "HAM", "nationality": "GBR", "team": "Ferrari", "points": "147"},
        {"position": "4", "name": "Charles Leclerc", "code": "LEC", "nationality": "MON", "team": "Ferrari", "points": "108"},
        {"position": "5", "name": "Lando Norris", "code": "NOR", "nationality": "GBR", "team": "McLaren", "points": "97"},
        {"position": "6", "name": "Oscar Piastri", "code": "PIA", "nationality": "AUS", "team": "McLaren", "points": "82"},
        {"position": "7", "name": "Max Verstappen", "code": "VER", "nationality": "NED", "team": "Red Bull Racing", "points": "76"},
        {"position": "8", "name": "Isack Hadjar", "code": "HAD", "nationality": "FRA", "team": "Red Bull Racing", "points": "52"},
        {"position": "9", "name": "Pierre Gasly", "code": "GAS", "nationality": "FRA", "team": "Alpine", "points": "41"},
        {"position": "10", "name": "Liam Lawson", "code": "LAW", "nationality": "NZL", "team": "Racing Bulls", "points": "30"},
        {"position": "11", "name": "Oliver Bearman", "code": "BEA", "nationality": "GBR", "team": "Haas F1 Team", "points": "18"},
        {"position": "12", "name": "Franco Colapinto", "code": "COL", "nationality": "ARG", "team": "Alpine", "points": "16"},
        {"position": "13", "name": "Arvid Lindblad", "code": "LIN", "nationality": "GBR", "team": "Racing Bulls", "points": "14"},
        {"position": "14", "name": "Carlos Sainz", "code": "SAI", "nationality": "ESP", "team": "Williams", "points": "6"},
        {"position": "15", "name": "Alexander Albon", "code": "ALB", "nationality": "THA", "team": "Williams", "points": "5"},
        {"position": "16", "name": "Esteban Ocon", "code": "OCO", "nationality": "FRA", "team": "Haas F1 Team", "points": "3"},
        {"position": "17", "name": "Gabriel Bortoleto", "code": "BOR", "nationality": "BRA", "team": "Audi", "points": "2"},
        {"position": "18", "name": "Fernando Alonso", "code": "ALO", "nationality": "ESP", "team": "Aston Martin", "points": "1"},
        {"position": "19", "name": "Nico Hulkenberg", "code": "HUL", "nationality": "GER", "team": "Audi", "points": "0"},
        {"position": "20", "name": "Valtteri Bottas", "code": "BOT", "nationality": "FIN", "team": "Cadillac", "points": "0"},
        {"position": "21", "name": "Sergio Perez", "code": "PER", "nationality": "MEX", "team": "Cadillac", "points": "0"},
        {"position": "22", "name": "Lance Stroll", "code": "STR", "nationality": "CAN", "team": "Aston Martin", "points": "0"}
    ]
    return {"status": "success", "data": fallback_standings}