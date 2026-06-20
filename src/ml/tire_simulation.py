
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split

class F1TireStrategySim:
    def __init__(self):
        # 2026 models require slightly deeper and more robust trees to capture the 
        # complex interactions of Active Aero, 50/50 electrical splits, and narrower tires.
        self.model = xgb.XGBRegressor(
            n_estimators=350,        # Increased from 150 for massive dataset reliability
            learning_rate=0.03,      # Slower learning rate for smoother degradation curves
            max_depth=7,             # Deeper trees to catch exponential thermal cliffs
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42
        )
        self.is_trained = False
        
        # Expanded 2026 feature matrix
        self.features = [
            'lap_number', 'tire_age_laps', 'fuel_load_kg', 'compound_type', 
            'track_temp_c', 'ers_deployment_mode', 'active_aero_z_mode_pct', 'base_lap_time'
        ]

    def generate_2026_training_data(self, base_times: dict, samples: int = 15000) -> pd.DataFrame:
        """
        Generates a massive, highly reliable synthetic dataset mapped to 2026 regulations.
        - Accounts for narrower 2026 tires (sharper thermal cliffs).
        - Integrates 350kW MGU-K Boost modes and Active Aero (Z-Mode/X-Mode).
        """
        print(f"🧬 Generating {samples} rows of 2026-compliant telemetry data...")
        np.random.seed(42)
        records = []
        tracks = list(base_times.keys())
        
        for _ in range(samples):
            track = np.random.choice(tracks)
            base_time = base_times[track]
            
            lap = np.random.randint(1, 65)
            tire_age = np.random.randint(1, lap + 1)
            fuel = np.random.uniform(2, 100)  # 2026 cars carry max ~100kg fuel
            compound = np.random.randint(1, 4) # 1: Hard, 2: Medium, 3: Soft
            track_temp = np.random.uniform(25, 55)
            
            # 2026 ERS Modes: 1 (Harvest/Lift & Coast), 2 (Balanced 8.5MJ), 3 (Override/Boost)
            ers_mode = np.random.choice([1, 2, 3], p=[0.15, 0.75, 0.10])
            
            # Active Aero: Percentage of the lap spent in Z-Mode (Cornering downforce)
            aero_z_pct = np.random.uniform(0.4, 0.75) 
            
            # --- 2026 PHYSICS CALCULATIONS ---
            
            # 1. Narrower Tire Wear (Exponential cliffs implemented to fix 44-lap anomalies)
            if compound == 3:    # Soft
                wear = (tire_age ** 1.35) * 0.075
                if tire_age > 18: wear += (tire_age - 18) ** 1.8  # Violent thermal cliff
            elif compound == 2:  # Medium
                wear = (tire_age ** 1.15) * 0.04
                if tire_age > 28: wear += (tire_age - 28) ** 1.5
            else:                # Hard
                wear = (tire_age ** 0.95) * 0.02
                if tire_age > 45: wear += (tire_age - 45) ** 1.2
                
            # 2. Track Temp Penalty (Narrower tires blister faster over 40°C)
            temp_penalty = max(0, (track_temp - 40) * 0.04) if compound == 3 else 0
            
            # 3. Fuel Penalty (2026 cars are 768kg. 10kg fuel costs ~0.30s)
            fuel_penalty = (fuel / 10.0) * 0.30
            
            # 4. ERS & Active Aero Impacts
            ers_modifier = {1: 1.2, 2: 0.0, 3: -0.85}[ers_mode] # Boost is fast but drains battery
            aero_penalty = (0.6 - aero_z_pct) * 1.5             # Unoptimized aero setups cost pace
            
            actual_time = base_time + wear + fuel_penalty + temp_penalty + ers_modifier + aero_penalty + np.random.normal(0, 0.08)
            
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
        """Trains the XGBoost engine on the highly dense 2026 matrix."""
        target = 'actual_lap_time'
        
        X = training_data_df[self.features]
        y = training_data_df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        self.is_trained = True

    def simulate_stint(self, base_lap_time: float, starting_fuel_kg: float, compound: int, track_temp: float, laps: int, push_laps: list = None) -> pd.DataFrame:
        """
        Simulates a single distinct stint lap-by-lap using the trained XGBoost model.
        Maintains internal fuel burn and applies 2026 energy management tactics.
        """
        import pandas as pd
        if push_laps is None:
            push_laps = []
            
        if not hasattr(self, 'is_trained') or not self.is_trained:
            raise ValueError("Model must be trained before running a simulation.")
            
        records = []
        current_fuel = starting_fuel_kg
        fuel_burn_per_lap = 1.35  # Calibrated baseline per lap consumption
        
        for stint_lap in range(1, laps + 1):
            # 2026 ERS Tactical Deployment Options
            if stint_lap in push_laps:
                ers_label = 'Boost (350kW)'
                ers_int = 3
                aero_z = 0.60  # X-Mode: Low Drag Configuration
            else:
                ers_label = 'Balanced'
                ers_int = 2
                aero_z = 0.65  # Z-Mode: High Downforce Cornering Configuration
                
            feature_dict = {
                'lap_number': stint_lap,
                'tire_age_laps': stint_lap,
                'fuel_load_kg': current_fuel,
                'compound_type': compound,
                'track_temp_c': track_temp,
                'base_lap_time': base_lap_time,
                'ers_deployment_mode': ers_int,
                'active_aero_z_mode_pct': aero_z
            }
            
            # Dynamic Feature Alignment: Ensures matrix shapes always match XGBoost expectations
            df_features = pd.DataFrame([feature_dict])
            if hasattr(self.model, 'feature_names_in_'):
                missing_cols = [c for c in self.model.feature_names_in_ if c not in df_features.columns]
                for mc in missing_cols:
                    df_features[mc] = 0.0
                df_features = df_features[self.model.feature_names_in_]
            
            predicted_time = self.model.predict(df_features)[0]
            
            records.append({
                'lap_number': stint_lap,
                'predicted_lap_time': predicted_time,
                'ers_mode': ers_label
            })
            
            current_fuel = max(0.0, current_fuel - fuel_burn_per_lap)
            
        return pd.DataFrame(records)