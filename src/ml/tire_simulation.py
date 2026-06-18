import pandas as pd   #type: ignore
import numpy as np      #type: ignore
import xgboost as xgb   #type: ignore
from sklearn.model_selection import train_test_split    #type: ignore

class F1TireStrategySim:
    def __init__(self):
        # Initialize an XGBoost Regressor tuned for F1 telemetry
        self.model = xgb.XGBRegressor(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        self.is_trained = False

    def train(self, historical_telemetry_df: pd.DataFrame):
        """Trains the model on historical F1 physics data."""
        features = ['lap_number', 'fuel_load_kg', 'compound_type', 'track_temp_c', 'base_lap_time']
        target = 'actual_lap_time'
        
        X = historical_telemetry_df[features]
        y = historical_telemetry_df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        self.is_trained = True

    def simulate_stint(self, base_lap_time: float, starting_fuel_kg: float, compound: int, track_temp: float, laps: int) -> pd.DataFrame:
        """Runs a dynamic lap-by-lap inference simulation applying fuel weight crossover."""
        if not self.is_trained:
            raise ValueError("Model must be trained before running a stint simulation.")

        stint_data = []
        current_fuel = starting_fuel_kg
        
        # F1 cars burn roughly 1.6kg of fuel per lap
        fuel_burn_rate_per_lap = 1.6 
        
        for lap in range(1, laps + 1):
            # 1. State of the car for THIS specific lap
            lap_state = pd.DataFrame([{
                'lap_number': lap,
                'fuel_load_kg': current_fuel,
                'compound_type': compound,
                'track_temp_c': track_temp,
                'base_lap_time': base_lap_time
            }])
            
            # 2. Predict the lap time based on the current state
            predicted_time = self.model.predict(lap_state)[0]
            
            stint_data.append({
                'lap_number': lap,
                'fuel_load_kg': round(current_fuel, 2),
                'predicted_lap_time': round(predicted_time, 3)
            })
            
            # 3. Apply the physical fuel burn (car gets lighter for the next lap)
            current_fuel = max(0.0, current_fuel - fuel_burn_rate_per_lap)
            
        return pd.DataFrame(stint_data)