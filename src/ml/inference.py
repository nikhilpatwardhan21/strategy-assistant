import joblib
import pandas as pd
import numpy as np

class TireDegradationPredictor:
    def __init__(self, model_path="ml_models/tire_deg_model.pkl", features_path="ml_models/model_features.pkl"):
        self.model = joblib.load(model_path)
        self.features = joblib.load(features_path)

    def simulate_stint(self, current_lap: int, stint_length: int, compound: str):
        """Simulates lap-by-lap time progression as tires degrade."""
        simulated_laps = []
        
        for lap in range(1, stint_length + 1):
            # Formulate the feature input schema matching our training data structure
            input_data = {
                'LapNumber': current_lap + lap,
                'Stint': 2, # Example stint count
                'TyreLife': lap,
                'Compound_HARD': 1 if compound.upper() == 'HARD' else 0,
                'Compound_MEDIUM': 1 if compound.upper() == 'MEDIUM' else 0,
                'Compound_SOFT': 1 if compound.upper() == 'SOFT' else 0,
            }
            
            input_df = pd.DataFrame([input_data]).reindex(columns=self.features, fill_value=0)
            predicted_time = self.model.predict(input_df)[0]
            simulated_laps.append({"Lap": lap, "PredictedLapTime": round(predicted_time, 3)})
            
        return simulated_laps