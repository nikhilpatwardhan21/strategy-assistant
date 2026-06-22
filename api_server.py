from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from main import run_race_pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/simulate")
async def simulate(data: dict):
    # Extracts circuit and strategy from the React request
    circuit = data.get("circuit")
    strategy = data.get("strategy")
    
    # Calls your function and returns the data to React
    result = run_race_pipeline(circuit, strategy) 
    return {"data": result}