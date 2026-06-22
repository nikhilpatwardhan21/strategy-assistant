import { useState } from 'react';
import axios from 'axios';
import StintTable from './components/StintTable';

export default function App() {
  const [circuit, setCircuit] = useState('');
  const [strategy, setStrategy] = useState('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runSimulation = async () => {
    setLoading(true);
    setError('');
    setResults(null);
    try {
      const response = await axios.post(`http://localhost:8000/simulate`, {
        circuit,
        strategy
      });
      
      if (response.data.data.status === 'error') {
        setError(response.data.data.message);
      } else {
        setResults(response.data.data);
      }
    } catch (err) {
      console.error("Connection error:", err);
      setError("Failed to connect to the simulation engine. Is it running?");
    }
    setLoading(false);
  };

  // Helper function to color-code the tire compounds
  const getTireBadge = (compound: string) => {
    if (compound === 'SOFT') return 'bg-red-600 text-white border-red-800';
    if (compound === 'MEDIUM') return 'bg-yellow-400 text-black border-yellow-600';
    if (compound === 'HARD') return 'bg-slate-100 text-black border-slate-300';
    return 'bg-slate-700 text-white border-slate-900';
  };

  return (
    // Added pt-16 to push the main content down so the fixed ticker doesn't overlap it
    <div className="min-h-screen bg-slate-950 text-white p-8 pt-16 font-sans relative">
      
      {/* 1. Race Control Ticker */}
      <div className="w-full overflow-hidden bg-red-600 text-white font-mono text-xs font-bold py-1.5 border-b border-red-800 absolute top-0 left-0 z-50">
        <div className="animate-marquee whitespace-nowrap tracking-widest">
          RACE CONTROL: DRS ENABLED • TRACK TEMPERATURE 38°C • AIR TEMPERATURE 24°C • HUMIDITY 42% • NO RAIN EXPECTED FOR THE NEXT 30 MINUTES • YELLOW FLAG IN SECTOR 2 CLEARED
        </div>
      </div>

      <header className="mb-10 text-center">
        <h1 className="text-5xl font-black italic tracking-tighter text-red-600 drop-shadow-lg">
          F1 STRATEGY ENGINE
        </h1>
        <p className="text-slate-400 mt-2 font-medium tracking-wide text-sm uppercase">2026 Season Predictive Simulator</p>
        
        {/* 2. Pulsing "Live Telemetry" Indicators */}
        <div className="flex items-center justify-center gap-3 mt-6">
          <div className="flex items-center gap-2 bg-slate-900 px-3 py-1 rounded-full border border-slate-800 shadow-inner">
            <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
            <span className="text-green-500 font-mono text-xs font-bold tracking-widest">ENGINE ONLINE</span>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 px-3 py-1 rounded-full border border-slate-800 shadow-inner">
            <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)] delay-75"></div>
            <span className="text-red-500 font-mono text-xs font-bold tracking-widest">
              {loading ? 'RECEIVING DATA...' : 'AWAITING TELEMETRY'}
            </span>
          </div>
        </div>
      </header>

      {/* Input Section */}
      <section className="max-w-2xl mx-auto bg-slate-900 p-8 rounded-2xl border border-slate-800 shadow-2xl">
        <div className="space-y-6">
          <div>
            <label className="block text-xs uppercase tracking-widest text-slate-400 font-bold mb-2">Target Circuit</label>
            <input 
              className="w-full bg-slate-950 p-4 rounded-lg border border-slate-800 focus:border-red-500 outline-none transition-colors font-mono"
              placeholder="e.g. Monza"
              value={circuit}
              onChange={(e) => setCircuit(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-slate-400 font-bold mb-2">Strategy Plan (S:Laps, M:Laps, H:Laps)</label>
            <input 
              className="w-full bg-slate-950 p-4 rounded-lg border border-slate-800 focus:border-red-500 outline-none transition-colors font-mono"
              placeholder="e.g. S:23,H:30"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            />
          </div>
          
          {/* 3. Animated "Simulating" Progress Button */}
          <button 
            onClick={runSimulation}
            disabled={loading}
            className="w-full relative overflow-hidden bg-red-600 hover:bg-red-700 disabled:bg-slate-800 disabled:cursor-not-allowed py-4 rounded-lg font-black tracking-widest uppercase transition-all shadow-lg hover:shadow-red-600/20 group"
          >
            {loading ? (
              <>
                <span className="relative z-10 text-white">Calculating Strategy...</span>
                <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" 
                     style={{ 
                       backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, #ffffff 10px, #ffffff 20px)',
                       backgroundSize: '28px 28px',
                       animation: 'moveStripes 1s linear infinite' 
                     }}>
                </div>
                <style>{`
                  @keyframes moveStripes {
                    0% { background-position: 0 0; }
                    100% { background-position: 28px 0; }
                  }
                `}</style>
              </>
            ) : (
              'Run Simulation'
            )}
          </button>
        </div>
      </section>

      {/* Error Handling */}
      {error && (
        <div className="max-w-2xl mx-auto mt-6 bg-red-950/50 border border-red-900 text-red-400 p-4 rounded-lg text-center font-mono text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Results Dashboard */}
      {results && !loading && (
        <section className="max-w-4xl mx-auto mt-12 animate-fade-in">
          <div className="flex justify-between items-end mb-6 border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-3xl font-black italic">{results.circuit}</h2>
              <p className="text-slate-400 font-mono text-sm">Total Distance: {results.total_laps} Laps</p>
            </div>
            <div className="text-right">
              <span className="bg-green-900/30 text-green-400 border border-green-800 px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase">
                Simulation Complete
              </span>
            </div>
          </div>

          {/* Stint Table Rendered Here with Results Data */}
          <StintTable results={results} />

          {/* Existing Stint Detail Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
            {results.stints.map((stint: any) => (
              <div key={stint.stint_number} className="bg-slate-900 rounded-xl border border-slate-800 p-6 flex flex-col relative overflow-hidden group hover:border-slate-600 transition-colors">
                
                {/* Compound Badge */}
                <div className={`absolute top-0 right-0 m-4 px-3 py-1 rounded shadow-sm border font-black text-xs tracking-widest ${getTireBadge(stint.compound)}`}>
                  {stint.compound}
                </div>

                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4">Stint {stint.stint_number}</h3>
                
                <div className="space-y-4 font-mono text-sm">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Lap Window</span>
                    <span className="font-bold text-white text-lg">{stint.lap_range}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Average Pace</span>
                    <span className="text-white">{stint.avg_pace}</span>
                  </div>
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Tire Drop (Start → End)</span>
                    <span className="text-amber-400">{stint.tire_drop}</span>
                  </div>
                  {stint.pit_loss > 0 && (
                    <div className="flex justify-between items-center text-red-400 pt-2">
                      <span>Pit Stop Time Loss</span>
                      <span>+{stint.pit_loss}s</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}