import os
import sys
import pandas as pd
import numpy as np
import logging

# 1. THE ULTIMATE SILENCE: Completely crush all FastF1 and HTTP logging outputs
logging.getLogger("fastf1").propagate = False
logging.getLogger("urllib3").propagate = False
logging.getLogger("requests").propagate = False

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.CRITICAL)

import fastf1
os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')
fastf1.set_log_level('CRITICAL')

# 2. Path Patch
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def generate_calibrated_telemetry(circuit: str) -> pd.DataFrame:
    np.random.seed(42)
    records = []
    track_baselines = {
        "monza": 81.0,        
        "silverstone": 87.0,  
        "spa": 104.0,         
        "monaco": 71.0,       
        "bahrain": 91.0,
        "austria": 66.0      # <--- Added Austria Baseline
    }
    circuit_key = circuit.strip().lower()
    base_time = track_baselines.get(circuit_key, 85.0)
    
    for _ in range(1500):
        lap = np.random.randint(1, 45)
        fuel = np.random.uniform(5, 100)
        compound = np.random.randint(1, 4) 
        track_temp = np.random.uniform(25, 50)
        
        if compound == 3:    
            wear_factor = (lap ** 1.25) * 0.06
        elif compound == 2:  
            wear_factor = (lap ** 1.1) * 0.035
        else:                
            wear_factor = (lap ** 0.95) * 0.02
            
        fuel_penalty = (fuel / 10.0) * 0.35
        actual_time = base_time + wear_factor + fuel_penalty + np.random.normal(0, 0.05)
        records.append({
            'lap_number': lap, 'fuel_load_kg': fuel, 'compound_type': compound,
            'track_temp_c': track_temp, 'base_lap_time': base_time, 'actual_lap_time': actual_time
        })
    return pd.DataFrame(records)


def run_historical_query_pipeline(user_question: str, target_url: str = None):
    from src.vectordb.vector_store import F1VectorStoreManager
    vdb_manager = F1VectorStoreManager()
    if target_url:
        print(f"\n🚀 Live data scraping synchronizer triggered...")
        vdb_manager.ingest_live_web_data(url=target_url, source_id="live_feed_ingest")
    else:
        vdb_manager.add_historical_stats()

    print("\n🔍 Querying local ChromaDB rows for context...")
    retrieved_stats, metadata = vdb_manager.query_similar_context(user_question, n_results=5)
    prompt = f"[VERIFIED DATABASE CONTEXT]\n{retrieved_stats}\n[USER QUESTION]\n{user_question}"
    
    if not os.getenv("OPENAI_API_KEY"):
        print("💡 [OFFLINE MODE] OpenAI key missing. Skipping query response generation.")
        return {"strategy_briefing": None, "constructed_prompt": prompt}
        
    from src.llm.llm_client import OpenAIEngine
    response = OpenAIEngine().generate_response(prompt)
    print("\n" + "="*55 + "\n📊 DYNAMIC F1 LIVE ENGINE REPORT\n" + "="*55)
    print(response)
    print("="*55 + "\n")
    return {"strategy_briefing": response, "constructed_prompt": prompt}


def run_web_interactive_session(url: str):
    from src.vectordb.vector_store import F1VectorStoreManager
    vdb_manager = F1VectorStoreManager()
    print(f"\n🚀 Ingesting live data from target URL...")
    vdb_manager.ingest_live_web_data(url=url, source_id="live_feed_ingest")
    print("\n✅ Live page indexed. Ask your questions below (Type 'exit' to stop).")

    while True:
        user_question = input("\n🎙️ Ask a question: ").strip() 
        if not user_question: continue
        if user_question.lower() in {"quit", "exit", "q"}: break

        retrieved_stats, _ = vdb_manager.query_similar_context(user_question, n_results=5)
        prompt = f"Using context: {retrieved_stats}\nAnswer: {user_question}"
        
        if not os.getenv("OPENAI_API_KEY"):
            print("💡 [OFFLINE MODE] OpenAI API key missing.")
            continue
            
        from src.llm.llm_client import OpenAIEngine
        print("\n" + "="*55)
        print(OpenAIEngine().generate_response(prompt))
        print("="*55)


def run_strategy_pipeline(circuit: str, current_lap: int, compound_choice: str, target_stint: int):
    """Original single-stint telemetry pipeline."""
    print(f"\n🏎️  [STRATEGY ENGINE] Loading race profile for {circuit.upper()}...")
    from src.ml.tire_simulation import F1TireStrategySim 

    track_baselines = {
        "monza": 81.0, "silverstone": 87.0, "spa": 104.0, 
        "monaco": 71.0, "bahrain": 91.0, "yas marina circuit abu dhabi": 86.5,
        "austria": 66.0  # <--- Added Austria Baseline
    }
    sim_base_time = track_baselines.get(circuit.strip().lower(), 85.0)

    print(f"⚙️  Training live XGBoost Engine on 2026 Calibrated F1 Physics for {circuit}...")
    ml_engine = F1TireStrategySim()
    training_data = ml_engine.generate_2026_training_data(base_times=track_baselines, samples=15000) 
    ml_engine.train(training_data)

    compound_map = {"SOFT": 3, "MEDIUM": 2, "HARD": 1}
    compound_int = compound_map.get(compound_choice.upper(), 2)

    sim_df = ml_engine.simulate_stint(
        base_lap_time=sim_base_time, starting_fuel_kg=95.0, compound=compound_int,
        track_temp=30.0, laps=target_stint, push_laps=[14, 15, 16] 
    )
    
    print("\n" + "═"*70)
    print(f"📊 ML TELEMETRY STINT FORECAST: {circuit.upper()} ({compound_choice.upper()})")
    print("═"*70)
    print(f"{'Lap':<5} │ {'Raw Time (s)':<15} │ {'Standard Time':<15} │ {'ERS Deployment Mode':<20}")
    print("─" * 70) 
    
    for _, row in sim_df.iterrows():
        lap = current_lap + int(row['lap_number']) - 1  
        raw_s = float(row['predicted_lap_time'])
        ers_mode = row['ers_mode']
        mins, secs = int(raw_s // 60), raw_s % 60
        print(f"{lap:<5} │ {raw_s:<15.3f} │ {mins}:{secs:06.3f} │ {ers_mode:<20}")
        
    print("═"*70 + "\n")
    if not os.getenv("OPENAI_API_KEY"):
        print("💡 [OFFLINE MODE] OpenAI API key not found. Skipping live AI briefing.\n")


# ==============================================================================
# NEW 2026 MULTI-STINT RACE ORCHESTRATOR
# ==============================================================================
def run_race_pipeline(circuit: str):
    """Full-race Pitstop Orchestrator using 2026 Regs (No edits to src folder needed)."""
    print(f"\n🏎️  [RACE ORCHESTRATOR] Loading full race profile for {circuit.upper()}...")
    from src.ml.tire_simulation import F1TireStrategySim 

    track_baselines = {
        "monza": 81.0, "silverstone": 87.0, "spa": 104.0, 
        "monaco": 71.0, "bahrain": 91.0, "yas marina": 86.5,
        "austria": 66.0
    }
    
    circuit_key = circuit.strip().lower()
    sim_base_time = track_baselines.get(circuit_key, 85.0)
    
    print(f"⚙️  Training live XGBoost Engine on 2026 F1 Physics for {circuit}...")
    ml_engine = F1TireStrategySim()
    training_data = ml_engine.generate_2026_training_data(base_times=track_baselines, samples=15000) 
    ml_engine.train(training_data)

    # 1. 2026 Strategy Configuration (Austria Default = 2-Stop)
    if circuit_key == "austria":
        strategy_plan = [(3, 18), (2, 27), (2, 26)] # Soft(18) -> Medium(27) -> Medium(26)
        pit_loss = 20.5
        track_temp = 38.0
        print(f"\n🏁 STRATEGY LOADED: AUSTRIA (71 Laps | 2-Stop: S->M->M | {pit_loss}s Pit Loss)")
    else:
        strategy_plan = [(2, 20), (1, 35)] # Generic 1-Stop fallback
        pit_loss = 22.0
        track_temp = 30.0
        print(f"\n🏁 STRATEGY LOADED: {circuit.upper()} (55 Laps | 1-Stop: M->H | {pit_loss}s Pit Loss)")

    # 2. Seamlessly Chain Stints Together
    current_fuel = 95.0
    race_dfs = []
    
    for stint_idx, (compound_int, stint_laps) in enumerate(strategy_plan):
        
        # 2026 Tactics: Trigger 350kW Undercut Boosts on In-Laps and Out-Laps
        push_laps = []
        if stint_idx < len(strategy_plan) - 1:
            push_laps.append(stint_laps) # Boost before pitting
        if stint_idx > 0:
            push_laps.append(1) # Boost leaving the pits
            
        stint_df = ml_engine.simulate_stint(
            base_lap_time=sim_base_time, starting_fuel_kg=current_fuel,
            compound=compound_int, track_temp=track_temp, laps=stint_laps, push_laps=push_laps
        )
        
        # 3. Inject the physical pit-lane time penalty
        stint_df['is_pit_lap'] = False
        if stint_idx > 0:
            stint_df.at[0, 'predicted_lap_time'] += pit_loss
            stint_df.at[0, 'is_pit_lap'] = True
            
        stint_df['stint_number'] = stint_idx + 1
        stint_df['compound_name'] = {3: 'SOFT', 2: 'MEDIUM', 1: 'HARD'}[compound_int]
        race_dfs.append(stint_df)
        
        # Lower fuel weight for the next stint (Austria ~1.35kg per lap)
        current_fuel = max(0.0, current_fuel - (1.35 * stint_laps))

    # 4. Compile the full 71-lap dataset
    full_race_df = pd.concat(race_dfs, ignore_index=True)
    full_race_df['overall_lap'] = range(1, len(full_race_df) + 1)

    # 5. Output Sleek Executive Summary
    total_race_time = full_race_df['predicted_lap_time'].sum()
    total_mins = int(total_race_time // 60)
    total_secs = total_race_time % 60
    hours = total_mins // 60
    rem_mins = total_mins % 60
    
    def format_time(raw_s):
        """Helper to format seconds into M:SS.mmm"""
        return f"{int(raw_s // 60)}:{raw_s % 60:06.3f}"

    compound_colors = {'SOFT': '🔴', 'MEDIUM': '🟡', 'HARD': '⚪'}
    strategy_str = " ➔ ".join([f"{compound_colors[{3: 'SOFT', 2: 'MEDIUM', 1: 'HARD'}[c]]} { {3: 'SOFT', 2: 'MEDIUM', 1: 'HARD'}[c] }" for c, _ in strategy_plan])
    stops = len(strategy_plan) - 1

    print("\n" + "═"*75)
    print(f"🏆 2026 STRATEGY SUMMARY: {circuit.upper()} ({len(full_race_df)} Laps)")
    print("═"*75)
    print(f"⏱️  PROJECTED RACE TIME : {hours}h {rem_mins}m {total_secs:.3f}s")
    print(f"🔄 STRATEGY PLAN      : {stops}-Stop [{strategy_str}]")
    print("─" * 75)

    # Group by Stint for a clean summary
    for stint_idx in full_race_df['stint_number'].unique():
        stint_data = full_race_df[full_race_df['stint_number'] == stint_idx]
        
        start_lap = stint_data['overall_lap'].min()
        end_lap = stint_data['overall_lap'].max()
        laps_count = len(stint_data)
        compound = stint_data['compound_name'].iloc[0]
        color = compound_colors.get(compound, '')
        
        # Calculate true pace (ignoring the slow pit lane lap and the fast ERS boost lap)
        clean_laps = stint_data[(stint_data['is_pit_lap'] == False) & (stint_data['ers_mode'] != 'Boost (350kW)')]
        
        if not clean_laps.empty:
            avg_pace = clean_laps['predicted_lap_time'].mean()
            start_pace = clean_laps['predicted_lap_time'].iloc[0]  # Fresh tires
            end_pace = clean_laps['predicted_lap_time'].iloc[-1]   # Old tires
        else:
            avg_pace = start_pace = end_pace = stint_data['predicted_lap_time'].mean()
            
        print(f"\n▶ [ STINT {stint_idx} ] Laps {start_lap}-{end_lap} ({laps_count} Laps) | {color} {compound}")
        print(f"  ├─ Avg Pace   : {format_time(avg_pace)}")
        print(f"  ├─ Tire Drop  : {format_time(start_pace)} ➔ {format_time(end_pace)} (Degradation + Fuel Burn)")
        
        # Highlight strategic actions
        if stint_idx < len(strategy_plan): # If not the final stint
             print(f"  └─ ⚡ Lap {end_lap}: 350kW Undercut Boost Activated (In-Lap)")
             
             next_compound = full_race_df[full_race_df['stint_number'] == stint_idx + 1]['compound_name'].iloc[0]
             next_color = compound_colors.get(next_compound, '')
             print(f"\n  🔧 PIT STOP {stint_idx} (Lap {end_lap + 1}) | +{pit_loss}s Time Loss | Fitted {next_color} {next_compound}")

    print("\n🏁 CHECKERED FLAG")
    print("═"*75 + "\n")


# ==============================================================================
# MAIN CLI MENU & EXECUTION BLOCK
# ==============================================================================
def main():
    print("\n" + "═"*70)
    print("🏎️   F1 STRATEGY & ANCHOR RAG ENGINE")
    print("═"*70)
    print(" [sim]  Run Single-Stint ML Telemetry Simulation")
    print(" [race] Run Full-Race Strategy Orchestrator (2026 Pitstops)")
    print(" [web]  Trigger Live Automated Data Ingestion")
    print("─" * 70)
    
    mode = input("👉 Select mode: ").strip().lower()
    
    if mode == 'sim':
        circuit = input("📍 Target Circuit (Try 'Austria'): ").strip()
        run_strategy_pipeline(circuit, current_lap=1, compound_choice="MEDIUM", target_stint=15)
    elif mode == 'race':
        circuit = input("📍 Target Circuit (Try 'Austria'): ").strip()
        run_race_pipeline(circuit)
    elif mode == 'web':
        url = input("🌐 Enter F1 live URL: ").strip()
        run_web_interactive_session(url)
    else:
        print("❌ Invalid mode selected. Please run the script again and type 'sim', 'race', or 'web'.")

if __name__ == "__main__":
    main()