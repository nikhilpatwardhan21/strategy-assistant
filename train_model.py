import os
import fastf1
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

print("--- Starting ML Model Training Pipeline ---")

# 1. Setup local folders explicitly before fastf1 can complain
os.makedirs("ml_models", exist_ok=True)
os.makedirs("f1_cache", exist_ok=True)  # <-- ADD THIS LINE HERE

fastf1.Cache.enable_cache('./f1_cache')

# 2. Pull actual telemetry data using FastF1 API
# We will use the 2024 British Grand Prix (Silverstone) as our training baseline
print("Fetching F1 telemetry data from Silverstone... (This may take a minute first time)")
session = fastf1.get_session(2024, 'Silverstone', 'R')
session.load(laps=True, weather=False)

# 3. Clean and process data columns
laps = session.laps.copy()
laps['LapTime_Sec'] = laps['LapTime'].dt.total_seconds()

# Filter out empty or corrupted rows
df = laps[['LapNumber', 'Stint', 'Compound', 'TyreLife', 'LapTime_Sec']].dropna()

# One-hot encode categorical tire compounds (SOFT, MEDIUM, HARD) to numbers
df = pd.get_dummies(df, columns=['Compound'])

# Ensure all standard columns exist even if a compound wasn't used much
for comp in ['Compound_SOFT', 'Compound_MEDIUM', 'Compound_HARD']:
    if comp not in df.columns:
        df[comp] = 0

# 4. Define our Input Features (X) and Target Label (y)
feature_cols = ['LapNumber', 'Stint', 'TyreLife', 'Compound_SOFT', 'Compound_MEDIUM', 'Compound_HARD']
X = df[feature_cols]
y = df['LapTime_Sec']

print(f"Training Data Summary: Extracted {len(df)} valid laps for training.")

# 5. Fit our Classical Supervised Regressor
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# 6. Save the serialization artifacts
joblib.dump(model, 'ml_models/tire_deg_model.pkl')
joblib.dump(feature_cols, 'ml_models/model_features.pkl')

print("--- ML Model Successfully Trained & Saved to ml_models/ ---")