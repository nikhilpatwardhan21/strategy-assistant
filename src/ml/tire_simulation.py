

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split

class F1TireStrategySim:
    def __init__(self):
        # 1. ML CALIBRATION: Less regularization, faster learning rate. 
        # This stops XGBoost from "smoothing" extreme high-fuel laps towards the middle.
        self.model = xgb.XGBRegressor(
            n_estimators=250,        
            learning_rate=0.08,      
            max_depth=8,             
            subsample=0.95,          
            colsample_bytree=1.0,    
            random_state=42
        )
        self.is_trained = False
        
        self.features = [
            'lap_number', 'tire_age_laps', 'fuel_load_kg', 'compound_type', 
            'track_temp_c', 'ers_deployment_mode', 'active_aero_z_mode_pct', 'base_lap_time'
        ]

    def generate_2026_training_data(self, base_times: dict, samples: int = 20000) -> pd.DataFrame:
        print(f"🧬 Generating {samples} rows of Reality-Calibrated 2026 telemetry data...")
        np.random.seed(42)
        records = []
        tracks = list(base_times.keys())
        
        for _ in range(samples):
            track = np.random.choice(tracks)
            base_time = base_times[track]
            
            # 2. BASELINE ANCHOR: Strip FastF1's median race wear to find "Zero Fuel" pace.
            calibrated_base_time = base_time - 2.5
            
            lap = np.random.randint(1, 72)
            tire_age = np.random.randint(0, lap + 2)
            fuel = np.random.uniform(0, 115)  
            compound = np.random.randint(1, 4) 
            track_temp = np.random.uniform(25, 55)
            
            ers_mode = np.random.choice([1, 2, 3], p=[0.15, 0.75, 0.10])
            aero_z_pct = np.random.uniform(0.4, 0.75) 
            
            profiles = {
                3: {'pace_offset': 0.0, 'wear_rate': 0.120, 'cliff_lap': 16, 'cliff_severity': 0.4},
                2: {'pace_offset': 0.7, 'wear_rate': 0.075, 'cliff_lap': 26, 'cliff_severity': 0.3},
                1: {'pace_offset': 1.4, 'wear_rate': 0.045, 'cliff_lap': 40, 'cliff_severity': 0.2}
            }
            prof = profiles[compound]
            
            wear = tire_age * prof['wear_rate']
            if tire_age > prof['cliff_lap']:
                laps_past_cliff = tire_age - prof['cliff_lap']
                cliff_penalty = min((laps_past_cliff ** 1.5) * prof['cliff_severity'], 6.5)
                wear += cliff_penalty
                
            # 3. SHORT TRACK CALIBRATION: ~0.025s per kg for a ~70s circuit
            fuel_penalty = fuel * 0.025
            
            ers_modifier = {1: 1.2, 2: 0.0, 3: -0.85}[ers_mode] 
            aero_penalty = (0.6 - aero_z_pct) * 1.5             
            
            actual_time = (calibrated_base_time + prof['pace_offset'] + wear + fuel_penalty + 
                        ers_modifier + aero_penalty + np.random.normal(0, 0.03))
            
            records.append({
                'lap_number': lap,
                'tire_age_laps': tire_age,
                'fuel_load_kg': fuel,
                'compound_type': compound,
                'track_temp_c': track_temp,
                'ers_deployment_mode': ers_mode,
                'active_aero_z_mode_pct': aero_z_pct,
                'base_lap_time': base_time,
                'actual_lap_time': actual_time
            })
            
        return pd.DataFrame(records)

    def train(self, training_data_df: pd.DataFrame):
        target = 'actual_lap_time'
        X = training_data_df[self.features]
        y = training_data_df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        self.is_trained = True

    def simulate_stint(self, base_lap_time: float, starting_fuel_kg: float, compound: int, track_temp: float, laps: int, push_laps: list = None) -> pd.DataFrame:
        import pandas as pd
        if push_laps is None: push_laps = []
        if not hasattr(self, 'is_trained') or not self.is_trained: raise ValueError("Model must be trained.")
            
        records = []
        current_fuel = starting_fuel_kg
        for stint_lap in range(1, laps + 1):
            if stint_lap in push_laps:
                ers_label,  ers_int, aero_z = 'Boost (350kW)', 3, 0.60
            else:
                ers_label, ers_int, aero_z = 'Balanced', 2, 0.65
                
            feature_dict = {
                'lap_number': stint_lap, 'tire_age_laps': stint_lap, 'fuel_load_kg': current_fuel,
                'compound_type': compound, 'track_temp_c': track_temp, 'base_lap_time': base_lap_time,
                'ers_deployment_mode': ers_int, 'active_aero_z_mode_pct': aero_z
            }
            df_features = pd.DataFrame([feature_dict])[self.model.feature_names_in_]
            predicted_time = self.model.predict(df_features)[0]
            records.append({'lap_number': stint_lap, 'predicted_lap_time': predicted_time, 'ers_mode': ers_label})
            current_fuel = max(0.0, current_fuel - 1.35)
        return pd.DataFrame(records)