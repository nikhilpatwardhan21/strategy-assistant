import fastf1

class F1DataLoader:
    def __init__(self, cache_dir="./f1_cache"):
        fastf1.Cache.enable_cache(cache_dir)
        
    def get_live_track_conditions(self, year: int, location: str):
        """Fetches ambient and track parameters for context building."""
        session = fastf1.get_session(year, location, 'R')
        session.load(laps=False, telemetry=False, weather=True)
        weather = session.weather_data
        
        return {
            "TrackTemp": weather['TrackTemp'].iloc[-1],
            "AirTemp": weather['AirTemp'].iloc[-1],
            "Rainfall": bool(weather['Rainfall'].iloc[-1])
        }