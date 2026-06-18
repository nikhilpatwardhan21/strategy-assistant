import os
import sys
import pandas as pd    #type: ignore
import numpy as np    #type: ignore

# 1. Path Patch: Forces Python to acknowledge your root workspace directory 
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_calibrated_telemetry(circuit: str) -> pd.DataFrame:
    """Generates physically calibrated telemetry mapped to specific F1 circuits."""
    np.random.seed(42)
    records = []
    
    # Map the user's circuit input to real-world F1 baseline lap times (in seconds)
    track_baselines = {
        "monza": 81.0,        # ~1:21.000
        "silverstone": 87.0,  # ~1:27.000
        "spa": 104.0,         # ~1:44.000
        "monaco": 71.0,       # ~1:11.000
        "bahrain": 91.0       # ~1:31.000
    }
    
    # Default to a standard 85-second track if the user types something unknown
    circuit_key = circuit.strip().lower()
    base_time = track_baselines.get(circuit_key, 85.0)
    
    for _ in range(1500):
        lap = np.random.randint(1, 45)
        fuel = np.random.uniform(5, 100)
        compound = np.random.randint(1, 4)  # 1: Hard, 2: Medium, 3: Soft
        track_temp = np.random.uniform(25, 50)
        
        # Calibrated wear coefficients
        if compound == 3:    # Soft
            wear_factor = (lap ** 1.25) * 0.06
        elif compound == 2:  # Medium
            wear_factor = (lap ** 1.1) * 0.035
        else:                # Hard
            wear_factor = (lap ** 0.95) * 0.02
            
        fuel_penalty = (fuel / 10.0) * 0.35
        
        actual_time = base_time + wear_factor + fuel_penalty + np.random.normal(0, 0.05)
        
        records.append({
            'lap_number': lap,
            'fuel_load_kg': fuel,
            'compound_type': compound,
            'track_temp_c': track_temp,
            'base_lap_time': base_time,
            'actual_lap_time': actual_time
        })
    return pd.DataFrame(records)

def run_historical_query_pipeline(user_question: str, target_url: str = None):
    from src.vectordb.vector_store import F1VectorStoreManager
    """Pipeline designed to answer historical or single-page web questions."""
    vdb_manager = F1VectorStoreManager()

    if target_url:
        print(f"\n🚀 [AUTOMATION ACTIVATED] Live data scraping synchronizer triggered...")
        vdb_manager.ingest_live_web_data(url=target_url, source_id="live_feed_ingest")
    else:
        vdb_manager.add_historical_stats()

    print("\n🔍 Querying local ChromaDB rows for your answer context...")
    retrieved_stats, metadata = vdb_manager.query_similar_context(user_question, n_results=5)
    
    # Show sources used for transparency
    print(f"\n📍 Sources retrieved: {len(metadata)} context blocks")
    for meta in metadata:
        source = meta.get('source_url') or meta.get('source', 'unknown')
        print(f"   - {source}")

    prompt = f"""
======================================================================
SYSTEM CONTEXT FOR HISTORICAL DATA ANALYST
======================================================================
You are an expert F1 Data Analyst. Answer the user's question using ONLY the verified context below.
Prioritize the content from the scraped page and avoid returning unrelated historical summaries.
If the requested year or specific prediction information is not present, say so clearly and summarize the nearest relevant information.

[VERIFIED DATABASE CONTEXT]
{retrieved_stats}

[USER QUESTION]
{user_question}

Provide a clean, engineering-focused layout response.
"""
    
    from src.llm.llm_client import OpenAIEngine
    ai_system = OpenAIEngine()
    response = ai_system.generate_response(prompt)
    
    print("\n======================================================================")
    print("📊 DYNAMIC F1 LIVE ENGINE REPORT")
    print("======================================================================")
    print(response)
    print("======================================================================\n")
    return {"strategy_briefing": response, "constructed_prompt": prompt}

def run_web_interactive_session(url: str):
    from src.vectordb.vector_store import F1VectorStoreManager
    from src.llm.llm_client import OpenAIEngine

    vdb_manager = F1VectorStoreManager()
    print(f"\n🚀 [AUTOMATION ACTIVATED] Live data scraping synchronizer triggered for: {url}")
    vdb_manager.ingest_live_web_data(url=url, source_id="live_feed_ingest")
    print("\n✅ Live page indexed. You can now ask multiple questions about this content.")
    print("Type 'quit' or 'exit' to stop the session.")

    ai_system = OpenAIEngine()
    while True:
        user_question = input("\nAsk a question about the scraped page: ").strip()
        if not user_question:
            continue
        if user_question.lower() in {"quit", "exit", "q"}:
            print("\n👋 Ending the interactive web session.")
            break

        print("\n🔍 Querying local ChromaDB rows for your answer context...")
        retrieved_stats, metadata = vdb_manager.query_similar_context(user_question, n_results=5)
        
        # Show sources used for transparency
        print(f"\n📍 Sources retrieved: {len(metadata)} context blocks")
        for meta in metadata:
            source = meta.get('source_url') or meta.get('source', 'unknown')
            print(f"   - {source}")

        prompt = f"""
======================================================================
SYSTEM CONTEXT FOR LIVE WEB DATA ANALYST
======================================================================
You are an expert F1 Data Analyst. Answer the user's question using ONLY the verified context below.
Prioritize the content from the scraped page and avoid returning unrelated historical summaries.
If the requested prediction or strategy detail is not present, state that clearly and summarize the nearest relevant information.

[VERIFIED DATABASE CONTEXT]
{retrieved_stats}

[USER QUESTION]
{user_question}

Provide a clean, engineering-focused layout response.
"""

        response = ai_system.generate_response(prompt)
        print("\n======================================================================")
        print("📊 DYNAMIC F1 LIVE ENGINE REPORT")
        print("======================================================================")
        print(response)
        print("======================================================================")

    return

def run_strategy_pipeline(circuit: str, current_lap: int, compound_choice: str, target_stint: int):
    """Our updated ML tire simulation pipeline driven by live XGBoost calibration."""
    print(f"\n--- [STRATEGY ENGINE] Analyzing Scenario for {circuit} ---")

    from src.ingestion.loader import F1DataLoader
    from src.vectordb.vector_store import F1VectorStoreManager
    from src.ml.tire_simulation import F1TireStrategySim 

    loader = F1DataLoader()
    try:
        weather_ctx = loader.get_live_track_conditions(2026, circuit)
        print(f"Track Status: Temp is {weather_ctx['TrackTemp']}°C | Ambient is {weather_ctx['AirTemp']}°C")
    except Exception:
        weather_ctx = {"TrackTemp": 26.2, "AirTemp": 16.0, "Rainfall": False}
        print("Track Status: Using baseline track telemetry (26.2°C)")

    print(f"⚙️  Training live XGBoost Engine on Calibrated F1 Physics for {circuit}...")
    ml_engine = F1TireStrategySim()
    
    # Pass the circuit name into the generator
    training_data = generate_calibrated_telemetry(circuit) 
    ml_engine.train(training_data)

    # Map the string input to the integer the model expects
    compound_map = {"SOFT": 3, "MEDIUM": 2, "HARD": 1}
    compound_int = compound_map.get(compound_choice.upper(), 2)

    # Determine the correct base time for the simulation execution
    track_baselines = {"monza": 81.0, "silverstone": 87.0, "spa": 104.0, "monaco": 71.0, "bahrain": 91.0}
    sim_base_time = track_baselines.get(circuit.strip().lower(), 85.0)

    # Execute model simulation
    sim_df = ml_engine.simulate_stint(
        base_lap_time=sim_base_time, 
        starting_fuel_kg=95.0,
        compound=compound_int,
        track_temp=weather_ctx['TrackTemp'],
        laps=target_stint
    )
    
    # Format structural outputs precisely
    predictions = []
    for _, row in sim_df.iterrows():
        predictions.append({
            'Lap': int(row['lap_number']),
            'PredictedLapTime': round(float(row['predicted_lap_time']), 3)
        })
    
    # --- BUILD CLEAN TERMINAL TABLE AND LLM STRING ---
    print("\n" + "="*55)
    print(f"📊 ML TIRE DEGRADATION FORECAST: {circuit.upper()} ({compound_choice.upper()})")
    print("="*55)
    print(f"{'Lap':<5} | {'Raw Time (s)':<15} | {'Standard Time':<15}")
    print("-" * 55)
    
    formatted_predictions_str = f"{'Lap':<5} | {'Raw Time (s)':<15} | {'Standard Time':<15}\n" + ("-" * 55) + "\n"
    
    for row in predictions:
        lap = current_lap + row['Lap'] - 1  # Align with current lap
        raw_s = row['PredictedLapTime']
        
        # Convert raw seconds into F1 Minutes:Seconds format
        mins = int(raw_s // 60)
        secs = raw_s % 60
        standard_time = f"{mins}:{secs:06.3f}"
        
        # Print to terminal
        row_str = f"{lap:<5} | {raw_s:<15.3f} | {standard_time:<15}"
        print(row_str)
        
        # Save to string for the AI prompt
        formatted_predictions_str += row_str + "\n"
        
    print("="*55 + "\n")
    
    vdb_manager = F1VectorStoreManager()
    query = "What rules apply to tire changes under a Safety Car?"
    regulatory_rules = vdb_manager.query_similar_context(query, n_results=1)
    
    prompt = f"""
======================================================================
SYSTEM CONTEXT FOR RACE STRATEGIST AI
======================================================================
You are the Lead Race Strategist for Scuderia Ferrari. Analyze the following race scenario:

[LIVE TELEMETRY DATA]
Circuit: {circuit}
Track Temperature: {weather_ctx['TrackTemp']}°C
Current Strategic Lap Marker: Lap {current_lap}

[ML MODEL DEGRADATION SIMULATIONS]
Target Compound Evaluation: {compound_choice.upper()}
Predicted Lap-by-Lap Times over the next {target_stint} laps:

{formatted_predictions_str}

[RETRIEVED FIA SPORTING CODES]
{regulatory_rules}

======================================================================
INSTRUCTIONS
======================================================================
Write a highly concise technical race strategy brief for the team principal. 
1. Evaluate the tire degradation slope shown in the ML metrics.
2. Cross-reference the retrieved FIA rules to confirm if a pitstop execution under these conditions is legal and strategically optimal.
3. Keep it engineering-focused and brief.
"""
    
    from src.llm.llm_client import OpenAIEngine
    ai_system = OpenAIEngine()
    briefing = ai_system.generate_response(prompt)
    
    print("\n======================================================================")
    print("FINAL RACE STRATEGY BRIEF GENERATED BY AI")
    print("======================================================================")
    print(briefing)
    print("======================================================================\n")
    return {"simulation_data": predictions, "strategy_briefing": briefing, "constructed_prompt": prompt}

if __name__ == "__main__":
    print("======================================================================")
    print("🏎️  WELCOME TO THE F1 INTERACTIVE ENGINE  🏎️")
    print("======================================================================")
    print("Options:")
    print("1. Type 'sim' to run an ML Tire Degradation Simulation Strategy.")
    print("2. Type 'web' to run the automated background live web ingestion.")
    print("----------------------------------------------------------------------")
    
    user_choice = input("What would you like to do? (Type 'sim' or 'web'): ").strip().lower()
    
    if user_choice == 'sim':
        circuit_input = input("Enter Circuit Name: ").strip()
        try:
            lap_input = int(input("Enter Current Lap Number (e.g., 1): "))
        except ValueError:
            lap_input = 1
        try:
            raw_stint = input("Enter Simulation Stint Length (Number of Laps): ")
            stint_input = int(float(raw_stint))
        except ValueError:
            stint_input = 12
        compound_input = input("Enter Target Compound (SOFT/MEDIUM/HARD): ").strip().upper()
        run_strategy_pipeline(circuit_input, lap_input, compound_input, stint_input)
        
    elif user_choice == 'web':
        default_url = "https://www.formula1.com/en/results/2026/races"
        run_web_interactive_session(default_url)
        
    else:
        print("⚠️ Invalid menu selection. Closing pipeline.")
        
    print("\n--- Pipeline Execution Completed Successfully ---")