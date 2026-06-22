# import os
# import sys
# import pandas as pd
# import numpy as np
# import logging

# # 1. THE ULTIMATE SILENCE
# logging.getLogger("fastf1").propagate = False
# logging.getLogger("urllib3").propagate = False
# logging.getLogger("requests").propagate = False
# for handler in logging.root.handlers[:]:
#     logging.root.removeHandler(handler)
# logging.basicConfig(level=logging.CRITICAL)

# import fastf1
# os.makedirs('cache', exist_ok=True)
# fastf1.Cache.enable_cache('cache')
# fastf1.set_log_level('CRITICAL')

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# # ==============================================================================
# # DYNAMIC FASTF1 TELEMETRY EXTRACTOR
# # ==============================================================================
# def fetch_real_track_data(circuit: str, year: int = 2024) -> dict:
#     print(f"\n📡 [API] Connecting to FastF1 for {circuit.upper()}...")
#     try:
#         session = fastf1.get_session(year, circuit, 'R')
#         session.load(telemetry=False, weather=True, messages=False)
#         total_laps = session.total_laps if session.total_laps > 0 else session.laps['LapNumber'].max()
#         clean_laps = session.laps.pick_quicklaps()
#         base_time = clean_laps['LapTime'].dt.total_seconds().median()
#         track_temp = session.weather_data['TrackTemp'].mean()
#         out_laps = session.laps[session.laps['PitOutTime'].notnull()]
#         pit_loss = (out_laps['LapTime'].dt.total_seconds().median() - base_time) if not out_laps.empty else 22.0
#         pit_loss = max(16.0, min(pit_loss, 28.0))
        
#         print(f"✅ [API] Success: {int(total_laps)} Laps | Pace: {base_time:.2f}s | Pit Loss: {pit_loss:.1f}s")
#         return {"base_time": float(base_time), "pit_loss": float(pit_loss), "total_laps": int(total_laps), "default_temp": float(track_temp)}
#     except Exception as e:
#         print(f"⚠️ [API] Fallback mode. Error: {e}")
#         return {"base_time": 85.0, "pit_loss": 22.0, "total_laps": 55, "default_temp": 30.0}

# # ==============================================================================
# # RACE ORCHESTRATOR
# # ==============================================================================
# def run_race_pipeline(circuit: str):
#     print(f"\n🏎️  [RACE ORCHESTRATOR] Loading full race profile for {circuit.upper()}...")
#     from src.ml.tire_simulation import F1TireStrategySim 

#     track_info = fetch_real_track_data(circuit)
#     sim_base_time, pit_loss, expected_total_laps, track_temp = track_info["base_time"], track_info["pit_loss"], track_info["total_laps"], track_info["default_temp"]
    
#     ml_engine = F1TireStrategySim()
#     ml_engine.train(ml_engine.generate_2026_training_data(base_times={circuit.lower(): sim_base_time}, samples=15000))

#     print(f"\n🚥 BUILD ENVIRONMENT STRATEGY FOR {circuit.upper()} ({expected_total_laps} Laps Expected)")
#     print(" Format: Compound:Laps (S=Soft, M=Medium, H=Hard separated by commas)")
    
#     while True:
#         strat_input = input("\n👉 Enter strategy plan: ").strip().upper()
#         try:
#             strategy_plan, total_strategy_laps = [], 0
#             for stint in strat_input.split(','):
#                 comp, laps = stint.strip().split(':')
#                 if comp not in {'S', 'M', 'H'}: raise ValueError("Use S, M, or H")
#                 strategy_plan.append(({'S': 3, 'M': 2, 'H': 1}[comp], int(laps)))
#                 total_strategy_laps += int(laps)
#             if total_strategy_laps == expected_total_laps: break
#             print(f"⚠️ MATH ERROR: Plan sums to {total_strategy_laps} laps (Expected {expected_total_laps}).")
#         except Exception as e:
#             print(f"❌ Syntax Error: {e}. Example: S:24,H:46")

#     # Simulation Logic
#     current_fuel, race_dfs = 95.0, []
#     for stint_idx, (compound_int, stint_laps) in enumerate(strategy_plan):
#         push_laps = [stint_laps] if stint_idx < len(strategy_plan)-1 else []
#         if stint_idx > 0: push_laps.append(1)
#         stint_df = ml_engine.simulate_stint(base_lap_time=sim_base_time, starting_fuel_kg=current_fuel, compound=compound_int, track_temp=track_temp, laps=stint_laps, push_laps=push_laps)
        
#         stint_df['is_pit_lap'] = False
#         if stint_idx > 0:
#             stint_df['predicted_lap_time'] = stint_df['predicted_lap_time'].astype(float)
#             stint_df.at[0, 'predicted_lap_time'] += pit_loss
#             stint_df.at[0, 'is_pit_lap'] = True
            
#         stint_df['stint_number'], stint_df['compound_name'] = stint_idx + 1, {3: 'SOFT', 2: 'MEDIUM', 1: 'HARD'}[compound_int]
#         race_dfs.append(stint_df)
#         current_fuel = max(0.0, current_fuel - (1.35 * stint_laps))

#     # Executive Summary Output
#     full_race_df = pd.concat(race_dfs, ignore_index=True)
#     full_race_df['overall_lap'] = range(1, len(full_race_df) + 1)
    
#     def format_time(raw_s): return f"{int(raw_s // 60)}:{raw_s % 60:06.3f}"
    
#     print("\n" + "═"*75 + f"\n🏆 2026 STRATEGY SUMMARY: {circuit.upper()}\n" + "═"*75)
#     for stint_idx in full_race_df['stint_number'].unique():
#         data = full_race_df[full_race_df['stint_number'] == stint_idx]
#         clean = data[(data['is_pit_lap'] == False) & (data['ers_mode'] != 'Boost (350kW)')]
        
#         print(f"\n▶ [ STINT {stint_idx} ] Laps {data['overall_lap'].min()}-{data['overall_lap'].max()} | 🔴🟡⚪ {data['compound_name'].iloc[0]}")
#         print(f"  ├─ Avg Pace   : {format_time(clean['predicted_lap_time'].mean())}")
#         print(f"  ├─ Tire Drop  : {format_time(clean['predicted_lap_time'].iloc[0])} ➔ {format_time(clean['predicted_lap_time'].iloc[-1])}")
        
#         if stint_idx < len(strategy_plan):
#             print(f"  └─ ⚡ Lap {data['overall_lap'].max()}: 350kW Undercut Boost")
#             print(f"\n  🔧 PIT STOP {stint_idx} (Lap {data['overall_lap'].max() + 1}) | +{pit_loss:.1f}s Time Loss")
#     print("\n🏁 CHECKERED FLAG\n" + "═"*75)

# # ==============================================================================
# # MAIN ENTRY POINT
# # ==============================================================================
# def main():
#     print("\n" + "═"*70 + "\n🏎️   F1 STRATEGY & ANCHOR RAG ENGINE\n" + "═"*70)
#     mode = input("👉 Select mode [race]: ").strip().lower()
#     if mode == 'race':
#         run_race_pipeline(input("📍 Target Circuit: ").strip())
#     else:
#         print("❌ Invalid mode.")

# if __name__ == "__main__":
#     main()

import os
import sys
import pandas as pd    #type:ignore
import numpy as np  #type:ignore
import logging

import fastf1        #type:ignore
# 1. THE ULTIMATE SILENCE
logging.getLogger("fastf1").propagate = False
logging.getLogger("urllib3").propagate = False
logging.getLogger("requests").propagate = False
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(level=logging.CRITICAL)

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')
fastf1.set_log_level('CRITICAL')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==============================================================================
# DYNAMIC FASTF1 TELEMETRY EXTRACTOR
# ==============================================================================
def fetch_real_track_data(circuit: str, year: int = 2024) -> dict:
    print(f"\n📡 [API] Connecting to FastF1 for {circuit.upper()}...")
    try:
        session = fastf1.get_session(year, circuit, 'R')
        session.load(telemetry=False, weather=True, messages=False)
        total_laps = session.total_laps if session.total_laps > 0 else session.laps['LapNumber'].max()
        clean_laps = session.laps.pick_quicklaps()
        base_time = clean_laps['LapTime'].dt.total_seconds().median()
        track_temp = session.weather_data['TrackTemp'].mean()
        out_laps = session.laps[session.laps['PitOutTime'].notnull()]
        pit_loss = (out_laps['LapTime'].dt.total_seconds().median() - base_time) if not out_laps.empty else 22.0
        pit_loss = max(16.0, min(pit_loss, 28.0))
        
        print(f"✅ [API] Success: {int(total_laps)} Laps | Pace: {base_time:.2f}s | Pit Loss: {pit_loss:.1f}s")
        return {"base_time": float(base_time), "pit_loss": float(pit_loss), "total_laps": int(total_laps), "default_temp": float(track_temp)}
    except Exception as e:
        print(f"⚠️ [API] Fallback mode. Error: {e}")
        return {"base_time": 85.0, "pit_loss": 22.0, "total_laps": 55, "default_temp": 30.0}

# ==============================================================================
# RACE ORCHESTRATOR
# ==============================================================================
def run_race_pipeline(circuit: str, strategy: str):
    print(f"\n🏎️  [RACE ORCHESTRATOR] Loading full race profile for {circuit.upper()}...")
    from src.ml.tire_simulation import F1TireStrategySim 

    track_info = fetch_real_track_data(circuit)
    sim_base_time, pit_loss, expected_total_laps, track_temp = track_info["base_time"], track_info["pit_loss"], track_info["total_laps"], track_info["default_temp"]
    
    ml_engine = F1TireStrategySim()
    ml_engine.train(ml_engine.generate_2026_training_data(base_times={circuit.lower(): sim_base_time}, samples=15000))

    # Parse the strategy string sent from the frontend
    strategy_plan, total_strategy_laps = [], 0
    try:
        for stint in strategy.upper().split(','):
            comp, laps = stint.strip().split(':')
            if comp not in {'S', 'M', 'H'}: 
                return {"status": "error", "message": f"Invalid compound '{comp}'. Use S, M, or H"}
            strategy_plan.append(({'S': 3, 'M': 2, 'H': 1}[comp], int(laps)))
            total_strategy_laps += int(laps)
        
        if total_strategy_laps != expected_total_laps:
            return {"status": "error", "message": f"Plan sums to {total_strategy_laps} laps, but {circuit.upper()} expects {expected_total_laps} laps."}
            
    except Exception as e:
        return {"status": "error", "message": f"Syntax Error: {e}. Example: S:24,H:46"}

    # Simulation Logic
    current_fuel, race_dfs = 95.0, []
    for stint_idx, (compound_int, stint_laps) in enumerate(strategy_plan):
        push_laps = [stint_laps] if stint_idx < len(strategy_plan)-1 else []
        if stint_idx > 0: push_laps.append(1)
        stint_df = ml_engine.simulate_stint(base_lap_time=sim_base_time, starting_fuel_kg=current_fuel, compound=compound_int, track_temp=track_temp, laps=stint_laps, push_laps=push_laps)
        
        stint_df['is_pit_lap'] = False
        if stint_idx > 0:
            stint_df['predicted_lap_time'] = stint_df['predicted_lap_time'].astype(float)
            stint_df.at[0, 'predicted_lap_time'] += pit_loss
            stint_df.at[0, 'is_pit_lap'] = True
            
        stint_df['stint_number'], stint_df['compound_name'] = stint_idx + 1, {3: 'SOFT', 2: 'MEDIUM', 1: 'HARD'}[compound_int]
        race_dfs.append(stint_df)
        current_fuel = max(0.0, current_fuel - (1.35 * stint_laps))

    # Executive Summary Formatting (Converts pandas to JSON)
    full_race_df = pd.concat(race_dfs, ignore_index=True)
    full_race_df['overall_lap'] = range(1, len(full_race_df) + 1)
    
    def format_time(raw_s): return f"{int(raw_s // 60)}:{raw_s % 60:06.3f}"
    
    response_payload = {
        "status": "success",
        "circuit": circuit.upper(),
        "total_laps": expected_total_laps,
        "stints": []
    }

    for stint_idx in full_race_df['stint_number'].unique():
        data = full_race_df[full_race_df['stint_number'] == stint_idx]
        clean = data[(data['is_pit_lap'] == False) & (data['ers_mode'] != 'Boost (350kW)')]
        
        response_payload["stints"].append({
            "stint_number": int(stint_idx),
            "lap_range": f"{data['overall_lap'].min()}-{data['overall_lap'].max()}",
            "compound": data['compound_name'].iloc[0],
            "avg_pace": format_time(clean['predicted_lap_time'].mean()),
            "tire_drop": f"{format_time(clean['predicted_lap_time'].iloc[0])} ➔ {format_time(clean['predicted_lap_time'].iloc[-1])}",
            "pit_loss": round(pit_loss, 1) if stint_idx > 1 else 0
        })

    return response_payload

# ==============================================================================
# MAIN ENTRY POINT (If run directly via terminal)
# ==============================================================================
def main():
    print("\n" + "═"*70 + "\n🏎️   F1 STRATEGY & ANCHOR RAG ENGINE\n" + "═"*70)
    mode = input("👉 Select mode [race]: ").strip().lower()
    if mode == 'race':
        circuit = input("📍 Target Circuit: ").strip()
        strategy = input("👉 Enter strategy plan (e.g., S:24,H:29): ").strip()
        result = run_race_pipeline(circuit, strategy)
        import json
        print("\n🏁 FINAL JSON RESULT:\n" + json.dumps(result, indent=2))
    else:
        print("❌ Invalid mode.")

if __name__ == "__main__":
    main()