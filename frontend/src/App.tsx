import { useState, useEffect } from 'react';
import axios from 'axios';
import StintTable from './components/StintTable';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 1. F1 Team Livery Configuration
interface Livery {
  id: string;
  name: string;
  primary: string;      // Accent Color (e.g., Turquoise, Scarlet, Orange)
  secondary: string;    // Secondary details
  glow: string;         // Box glow RGB
  bgAccent: string;     // Tailwind BG class
  textClass: string;    // Tailwind Text class
  logo: string;
}

const LIVERIES: Livery[] = [
  { id: 'f1', name: 'F1 Standard', primary: '#e10600', secondary: '#ffffff', glow: 'rgba(225, 6, 0, 0.4)', bgAccent: 'bg-red-600', textClass: 'text-red-500', logo: '🏎️' },
  { id: 'ferrari', name: 'Ferrari', primary: '#ff1801', secondary: '#facc15', glow: 'rgba(255, 24, 1, 0.4)', bgAccent: 'bg-red-600', textClass: 'text-red-500', logo: '🇮🇹' },
  { id: 'redbull', name: 'Red Bull', primary: '#facc15', secondary: '#0f172a', glow: 'rgba(250, 204, 21, 0.4)', bgAccent: 'bg-yellow-500', textClass: 'text-yellow-400', logo: '🐂' },
  { id: 'mercedes', name: 'Mercedes', primary: '#00ffc4', secondary: '#000000', glow: 'rgba(0, 255, 196, 0.4)', bgAccent: 'bg-teal-500', textClass: 'text-teal-400', logo: '⭐' },
  { id: 'mclaren', name: 'McLaren', primary: '#ff8700', secondary: '#0984e3', glow: 'rgba(255, 135, 0, 0.4)', bgAccent: 'bg-orange-500', textClass: 'text-orange-500', logo: '🧡' },
  { id: 'aston', name: 'Aston Martin', primary: '#c5e82a', secondary: '#004225', glow: 'rgba(197, 232, 42, 0.4)', bgAccent: 'bg-lime-500', textClass: 'text-lime-400', logo: '🟢' }
];

// 2. Circuit Registry with stylized SVG outline coordinates
interface Circuit {
  id: string;
  name: string;
  displayName: string;
  country: string;
  laps: number;
  length: string;
  type: string;
  flag: string;
  temp: number;
  path: string; // SVG path inside a 100x100 box
}

const CIRCUITS: Circuit[] = [
  { id: 'monza', name: 'Italian GP', displayName: 'Monza', country: 'Italy', laps: 53, length: '5.793 km', type: 'High Speed', flag: '🇮🇹', temp: 38, path: 'M 25 75 L 25 30 L 30 25 L 45 25 L 50 35 L 55 25 L 75 25 L 85 35 L 85 70 Q 80 85 50 85 Z' },
  { id: 'spa', name: 'Belgian GP', displayName: 'Spa-Francorchamps', country: 'Belgium', laps: 44, length: '7.004 km', type: 'Elevation / Fast', flag: '🇧🇪', temp: 22, path: 'M 35 80 L 15 65 L 20 40 L 40 40 L 48 15 L 68 25 L 50 48 L 78 45 L 88 70 L 72 85 L 50 68 Z' },
  { id: 'monaco', name: 'Monaco GP', displayName: 'Monaco', country: 'Monaco', laps: 78, length: '3.337 km', type: 'Tight Street', flag: '🇲🇨', temp: 28, path: 'M 15 65 L 35 45 L 50 30 L 60 40 L 52 55 L 62 70 L 75 62 L 88 50 L 78 85 L 45 80 L 30 75 Z' },
  { id: 'silverstone', name: 'British GP', displayName: 'Silverstone', country: 'United Kingdom', laps: 52, length: '5.891 km', type: 'High Speed', flag: '🇬🇧', temp: 24, path: 'M 15 45 L 30 15 L 55 20 L 65 10 L 80 32 L 88 48 L 72 70 L 52 62 L 35 78 L 22 68 Z' },
  { id: 'suzuka', name: 'Japanese GP', displayName: 'Suzuka', country: 'Japan', laps: 53, length: '5.807 km', type: 'Technical / Corners', flag: '🇯🇵', temp: 26, path: 'M 25 25 C 40 25 45 48 55 48 C 65 48 80 25 80 40 C 80 55 65 48 55 48 C 45 48 40 75 25 75 C 10 75 10 25 25 25' },
  { id: 'bahrain', name: 'Bahrain GP', displayName: 'Sakhir', country: 'Bahrain', laps: 57, length: '5.412 km', type: 'Braking / Traction', flag: '🇧🇭', temp: 35, path: 'M 15 80 L 15 15 L 40 15 L 40 38 L 65 38 L 65 60 L 85 60 L 85 80 Z' },
  { id: 'singapore', name: 'Singapore GP', displayName: 'Marina Bay', country: 'Singapore', laps: 62, length: '4.940 km', type: 'Street Circuit', flag: '🇸🇬', temp: 32, path: 'M 15 15 L 85 15 L 85 45 L 70 45 L 70 78 L 50 78 L 50 45 L 30 45 L 30 78 L 15 78 Z' },
  { id: 'zandvoort', name: 'Dutch GP', displayName: 'Zandvoort', country: 'Netherlands', laps: 72, length: '4.259 km', type: 'Banked Curves', flag: '🇳🇱', temp: 20, path: 'M 20 80 L 20 20 Q 50 15 85 30 L 85 65 Q 50 85 20 80 Z' },
  { id: 'melbourne', name: 'Australian GP', displayName: 'Albert Park', country: 'Australia', laps: 58, length: '5.278 km', type: 'Semi-Street', flag: '🇦🇺', temp: 25, path: 'M 15 80 L 15 15 L 85 15 L 85 48 L 50 48 L 50 80 Z' },
  { id: 'interlagos', name: 'Brazilian GP', displayName: 'Interlagos', country: 'Brazil', laps: 71, length: '4.309 km', type: 'Elevation / Short', flag: '🇧🇷', temp: 27, path: 'M 35 80 L 15 48 L 45 15 L 85 15 L 85 55 L 60 80 Z' }
];

interface StintInput {
  compound: 'SOFT' | 'MEDIUM' | 'HARD';
  laps: number;
}

export default function App() {
  const [selectedCircuit, setSelectedCircuit] = useState<Circuit>(CIRCUITS[0]);
  const [activeLivery, setActiveLivery] = useState<Livery>(LIVERIES[0]);
  const [stints, setStints] = useState<StintInput[]>([
    { compound: 'MEDIUM', laps: 21 },
    { compound: 'HARD', laps: 32 }
  ]);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Tab control: 'telemetry' | 'qa'
  const [activeTab, setActiveTab] = useState<'telemetry' | 'qa'>('telemetry');

  // Hover & Telemetry connection online states
  const [hoveredLap, setHoveredLap] = useState<any>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [isOutdated, setIsOutdated] = useState(false);

  // 2026 Standings state
  const [standings, setStandings] = useState<any[]>([]);
  const [standingsLoading, setStandingsLoading] = useState(false);

  // RAG states
  const [urlInput, setUrlInput] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  
  const [qaInput, setQaInput] = useState('');
  const [submittingQa, setSubmittingQa] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'assistant', text: string, sources?: string[] }>>([
    { role: 'assistant', text: 'F1 DECISION SUPPORT BOT ONLINE // Historical database loaded. Ask me about champions, qualifyings, historical eras, or paste an F1 URL above to feed me live text data.' }
  ]);

  // Sync circuit change with default stints
  const handleCircuitChange = (circuitId: string) => {
    const circuit = CIRCUITS.find(c => c.id === circuitId);
    if (circuit) {
      setSelectedCircuit(circuit);
      // Config standard 1-stop strategy
      const medLaps = Math.round(circuit.laps * 0.4);
      const hardLaps = circuit.laps - medLaps;
      setStints([
        { compound: 'MEDIUM', laps: medLaps },
        { compound: 'HARD', laps: hardLaps }
      ]);
    }
  };

  // Test backend availability on mount
  useEffect(() => {
    const checkApi = async () => {
      try {
        await axios.post(`${API_BASE_URL}/simulate`, { circuit: 'Italian GP', strategy: 'M:21,H:32' });
        setApiOnline(true);
      } catch (err) {
        console.warn("Backend server not responding yet:", err);
        setApiOnline(false);
      }
    };
    checkApi();
  }, []);

  // Fetch 2026 Driver standings
  useEffect(() => {
    const fetchStandings = async () => {
      setStandingsLoading(true);
      try {
        const response = await axios.get(`${API_BASE_URL}/standings`);
        if (response.data.status === 'success') {
          setStandings(response.data.data);
        }
      } catch (err) {
        console.error("Failed to load standings:", err);
      }
      setStandingsLoading(false);
    };
    fetchStandings();
  }, []);

  // Run initial simulation on load automatically
  useEffect(() => {
    const autoSim = async () => {
      setLoading(true);
      try {
        const response = await axios.post(`${API_BASE_URL}/simulate`, {
          circuit: 'Italian GP',
          strategy: 'M:21,H:32'
        });
        const payload = response.data.data;
        if (payload.status !== 'error') {
          setResults(payload);
          if (payload.laps && payload.laps.length > 0) {
            setHoveredLap(payload.laps[0]);
          }
        }
      } catch (err) {
        console.error("Initial auto simulation failed:", err);
      }
      setLoading(false);
    };
    autoSim();
  }, []);

  // Set outdated state when inputs are modified
  useEffect(() => {
    if (results) {
      setIsOutdated(true);
    }
  }, [selectedCircuit, stints]);

  // Strategy preset appliers
  const loadPreset = (presetType: '1-stop-mh' | '1-stop-sh' | '2-stop-smm' | '2-stop-mhm') => {
    const total = selectedCircuit.laps;
    if (presetType === '1-stop-mh') {
      const med = Math.round(total * 0.4);
      setStints([
        { compound: 'MEDIUM', laps: med },
        { compound: 'HARD', laps: total - med }
      ]);
    } else if (presetType === '1-stop-sh') {
      const soft = Math.round(total * 0.3);
      setStints([
        { compound: 'SOFT', laps: soft },
        { compound: 'HARD', laps: total - soft }
      ]);
    } else if (presetType === '2-stop-smm') {
      const soft = Math.round(total * 0.25);
      const med1 = Math.round(total * 0.35);
      setStints([
        { compound: 'SOFT', laps: soft },
        { compound: 'MEDIUM', laps: med1 },
        { compound: 'MEDIUM', laps: total - soft - med1 }
      ]);
    } else if (presetType === '2-stop-mhm') {
      const med1 = Math.round(total * 0.3);
      const hard = Math.round(total * 0.4);
      setStints([
        { compound: 'MEDIUM', laps: med1 },
        { compound: 'HARD', laps: hard },
        { compound: 'MEDIUM', laps: total - med1 - hard }
      ]);
    }
  };

  // Stint modifiers
  const updateStintCompound = (index: number, compound: 'SOFT' | 'MEDIUM' | 'HARD') => {
    const updated = [...stints];
    updated[index].compound = compound;
    setStints(updated);
  };

  const updateStintLaps = (index: number, newLaps: number) => {
    const updated = [...stints];
    updated[index].laps = Math.max(1, newLaps);
    setStints(updated);
  };

  const addStint = () => {
    const totalAllocated = stints.reduce((sum, s) => sum + s.laps, 0);
    const remaining = Math.max(1, selectedCircuit.laps - totalAllocated);
    setStints([...stints, { compound: 'SOFT', laps: remaining }]);
  };

  const removeStint = (index: number) => {
    if (stints.length > 1) {
      setStints(stints.filter((_, i) => i !== index));
    }
  };

  const totalStintLaps = stints.reduce((sum, s) => sum + s.laps, 0);
  const lapDifference = totalStintLaps - selectedCircuit.laps;

  // Run Simulation API call
  const runSimulation = async () => {
    if (lapDifference !== 0) {
      setError(`Strategy lap math mismatch. Adjust stints to equal exactly ${selectedCircuit.laps} laps.`);
      return;
    }
    
    setLoading(true);
    setError('');
    setResults(null);
    setHoveredLap(null);

    const strategyString = stints.map(s => `${s.compound.charAt(0)}:${s.laps}`).join(',');

    try {
      const response = await axios.post(`${API_BASE_URL}/simulate`, {
        circuit: selectedCircuit.name, // sends GP Name
        strategy: strategyString
      });
      
      const payload = response.data.data;
      if (payload.status === 'error') {
        setError(payload.message);
      } else {
        setResults(payload);
        if (payload.laps && payload.laps.length > 0) {
          setHoveredLap(payload.laps[0]);
        }
        setApiOnline(true);
        setIsOutdated(false);
      }
    } catch (err) {
      console.error("Connection error:", err);
      setError(`Unable to connect to the simulation engine. Verify the backend is online at ${API_BASE_URL}.`);
      setApiOnline(false);
    }
    setLoading(false);
  };

  // URL Ingest
  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setIngesting(true);
    setIngestStatus('SCRAPING WEB TEXT...');
    try {
      const response = await axios.post(`${API_BASE_URL}/ingest`, { url: urlInput });
      if (response.data.status === 'success') {
        setIngestStatus('✅ INGESTION & VECTORIZATION COMPLETE');
        setUrlInput('');
      } else {
        setIngestStatus(`❌ ERROR: ${response.data.message}`);
      }
    } catch (err) {
      console.error(err);
      setIngestStatus('❌ LINKING FAILURE. TRY AGAIN.');
    }
    setIngesting(false);
  };

  // RAG Q&A Submit
  const handleQaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qaInput.trim()) return;
    const question = qaInput;
    setQaInput('');
    setSubmittingQa(true);
    
    // Add user message to history
    setChatHistory(prev => [...prev, { role: 'user', text: question }]);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, { question });
      if (response.data.status === 'success') {
        setChatHistory(prev => [...prev, { 
          role: 'assistant', 
          text: response.data.answer,
          sources: response.data.sources 
        }]);
      } else {
        setChatHistory(prev => [...prev, { role: 'assistant', text: `⚠️ Error: ${response.data.message}` }]);
      }
    } catch (err) {
      console.error(err);
      setChatHistory(prev => [...prev, { role: 'assistant', text: '❌ Could not retrieve context. Is python API running?' }]);
    }
    setSubmittingQa(false);
  };

  // F1 Sector timing calculation (Purple, Green, Yellow)
  const getSectorStats = (lap: any) => {
    if (!lap) return [];
    const t = lap.predicted_lap_time;
    const isBoost = lap.ers_mode === 'Boost (350kW)';
    const isPit = lap.is_pit_lap;
    
    let s1 = t * 0.31;
    let s2 = t * 0.35;
    let s3 = t * 0.34;
    
    let c1 = 'text-green-400';
    let c2 = 'text-green-400';
    let c3 = 'text-green-400';

    if (isPit) {
      s1 += 22; // Pitstop occurs in Sector 1
      c1 = 'text-yellow-500';
    } else if (isBoost) {
      s1 -= 0.15;
      s2 -= 0.45;
      s3 -= 0.25;
      c2 = 'text-purple-400'; // Fastest Sector
      c3 = 'text-purple-400';
    } else {
      if (lap.lap_in_stint > 16) c2 = 'text-yellow-500';
      if (lap.lap_in_stint > 26) c3 = 'text-yellow-500';
    }
    
    return [
      { name: 'S1', val: s1.toFixed(3), color: c1 },
      { name: 'S2', val: s2.toFixed(3), color: c2 },
      { name: 'S3', val: s3.toFixed(3), color: c3 }
    ];
  };

  // Helper colors
  const getCompoundColor = (compound: string) => {
    if (compound === 'SOFT') return '#ef4444';
    if (compound === 'MEDIUM') return '#eab308';
    if (compound === 'HARD') return '#f8fafc';
    return '#64748b';
  };

  const getCompoundTailwindBg = (compound: string) => {
    if (compound === 'SOFT') return 'bg-red-600 text-white border-red-800';
    if (compound === 'MEDIUM') return 'bg-yellow-500 text-black border-yellow-600';
    if (compound === 'HARD') return 'bg-slate-100 text-black border-slate-300';
    return 'bg-slate-700 text-white border-slate-900';
  };

  const formatTime = (timeInSeconds: number) => {
    if (!timeInSeconds) return '-';
    const mins = Math.floor(timeInSeconds / 60);
    const secs = (timeInSeconds % 60).toFixed(3);
    return `${mins}:${secs.padStart(6, '0')}`;
  };

  // Render SVG Telemetry Chart
  const renderTelemetryChart = () => {
    if (!results || !results.laps || results.laps.length === 0) return null;

    const laps = results.laps;
    const totalLaps = results.total_laps;

    const rawTimes = laps.map((l: any) => l.predicted_lap_time);
    const minTime = Math.min(...rawTimes);
    const maxTime = Math.max(...rawTimes);

    const graphMin = minTime - 0.5;
    const graphMax = maxTime + 1.0;

    const width = 780;
    const height = 230; // Compact height
    const padding = { top: 15, right: 15, bottom: 35, left: 60 };

    const getX = (lap: number) => {
      return padding.left + ((lap - 1) / (totalLaps - 1)) * (width - padding.left - padding.right);
    };

    const getY = (time: number) => {
      const val = Math.min(graphMax, Math.max(graphMin, time));
      return height - padding.bottom - ((val - graphMin) / (graphMax - graphMin)) * (height - padding.top - padding.bottom);
    };

    // Stint divisions for colored lines
    const stintsData: any[][] = [];
    laps.forEach((lap: any) => {
      if (stintsData.length === 0 || lap.stint_number !== stintsData[stintsData.length - 1][0].stint_number) {
        stintsData.push([lap]);
      } else {
        stintsData[stintsData.length - 1].push(lap);
      }
    });

    const stintPaths = stintsData.map((stintLaps) => {
      let pathD = '';
      let fillD = '';
      
      stintLaps.forEach((lap, i) => {
        const x = getX(lap.overall_lap);
        const y = getY(lap.predicted_lap_time);
        
        if (i === 0) {
          pathD = `M ${x} ${y}`;
          fillD = `M ${x} ${height - padding.bottom} L ${x} ${y}`;
        } else {
          pathD += ` L ${x} ${y}`;
          fillD += ` L ${x} ${y}`;
        }
        
        if (i === stintLaps.length - 1) {
          fillD += ` L ${x} ${height - padding.bottom} Z`;
        }
      });

      const compound = stintLaps[0].compound;
      return {
        pathD,
        fillD,
        color: getCompoundColor(compound),
        compound
      };
    });

    // Axis values
    const lapTicks = [];
    const step = Math.ceil(totalLaps / 8);
    for (let i = 1; i <= totalLaps; i += step) {
      lapTicks.push(i);
    }
    if (lapTicks[lapTicks.length - 1] !== totalLaps) {
      lapTicks.push(totalLaps);
    }

    const timeTicks = [];
    const timeStep = (graphMax - graphMin) / 4;
    for (let i = 0; i <= 4; i++) {
      timeTicks.push(graphMin + i * timeStep);
    }

    return (
      <div 
        className="relative bg-slate-950/40 border rounded-xl p-3 f1-grid glass-panel"
        style={{ borderColor: `${activeLivery.primary}40`, boxShadow: `0 0 15px ${activeLivery.glow}` }}
      >
        <div className="flex justify-between items-center mb-2">
          <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 font-display">TELEMETRY DEGRADATION GRAPH</span>
          {hoveredLap && (
            <div className="text-[9px] font-telemetry flex gap-3 bg-slate-950 px-2.5 py-0.5 rounded border border-slate-800">
              <span>LAP: <strong className="text-white">{hoveredLap.overall_lap}</strong></span>
              <span>PACE: <strong className="text-green-400">{formatTime(hoveredLap.predicted_lap_time)}</strong></span>
              <span>AGE: <strong style={{ color: getCompoundColor(hoveredLap.compound) }}>{hoveredLap.lap_in_stint}L</strong></span>
              <span>ERS: <strong className="text-purple-400">{hoveredLap.ers_mode}</strong></span>
            </div>
          )}
        </div>
        
        <svg className="w-full h-auto" viewBox={`0 0 ${width} ${height}`} width="100%">
          <defs>
            <linearGradient id="grad-SOFT" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.2"/>
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0"/>
            </linearGradient>
            <linearGradient id="grad-MEDIUM" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#eab308" stopOpacity="0.2"/>
              <stop offset="100%" stopColor="#eab308" stopOpacity="0.0"/>
            </linearGradient>
            <linearGradient id="grad-HARD" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f8fafc" stopOpacity="0.15"/>
              <stop offset="100%" stopColor="#f8fafc" stopOpacity="0.0"/>
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {timeTicks.map((time, idx) => (
            <g key={idx}>
              <line x1={padding.left} y1={getY(time)} x2={width - padding.right} y2={getY(time)} stroke="rgba(30, 41, 59, 0.4)" strokeDasharray="3 3"/>
              <text x={padding.left - 8} y={getY(time) + 3} fill="#64748b" fontSize="9" fontFamily="Share Tech Mono" textAnchor="end">
                {formatTime(time).slice(0, -1)}
              </text>
            </g>
          ))}

          {lapTicks.map((lap, idx) => (
            <g key={idx}>
              <line x1={getX(lap)} y1={padding.top} x2={getX(lap)} y2={height - padding.bottom} stroke="rgba(30, 41, 59, 0.4)" strokeDasharray="3 3"/>
              <text x={getX(lap)} y={height - padding.bottom + 14} fill="#64748b" fontSize="9" fontFamily="Share Tech Mono" textAnchor="middle">
                L{lap}
              </text>
            </g>
          ))}

          {/* Pit Stop Indicators */}
          {laps.map((lap: any, idx: number) => {
            if (lap.is_pit_lap) {
              const x = getX(lap.overall_lap);
              return (
                <g key={idx}>
                  <line x1={x} y1={padding.top} x2={x} y2={height - padding.bottom} stroke="#ef4444" strokeWidth="1" strokeDasharray="2 2"/>
                  <rect x={x - 18} y={padding.top + 3} width="36" height="12" rx="2" fill="#e10600"/>
                  <text x={x} y={padding.top + 12} fill="#ffffff" fontSize="7" fontFamily="Inter" fontWeight="900" textAnchor="middle">PIT</text>
                </g>
              );
            }
            return null;
          })}

          {/* Paths */}
          {stintPaths.map((sp, idx) => (
            <path key={`fill-${idx}`} d={sp.fillD} fill={`url(#grad-${sp.compound})`}/>
          ))}

          {stintPaths.map((sp, idx) => (
            <path key={`line-${idx}`} d={sp.pathD} fill="none" stroke={sp.color} strokeWidth="3" strokeLinecap="round"/>
          ))}

          {/* Hover guidelines */}
          {hoveredLap && (
            <g>
              <line x1={getX(hoveredLap.overall_lap)} y1={padding.top} x2={getX(hoveredLap.overall_lap)} y2={height - padding.bottom} stroke={activeLivery.primary} strokeWidth="1" strokeDasharray="2 2"/>
              <circle cx={getX(hoveredLap.overall_lap)} cy={getY(hoveredLap.predicted_lap_time)} r="5" fill={getCompoundColor(hoveredLap.compound)} stroke="#06080e" strokeWidth="2"/>
            </g>
          )}

          {/* Hover overlay triggers */}
          {laps.map((lap: any, idx: number) => {
            const rWidth = (width - padding.left - padding.right) / (totalLaps - 1);
            return (
              <rect 
                key={idx}
                x={getX(lap.overall_lap) - rWidth / 2} 
                y={padding.top} 
                width={rWidth} 
                height={height - padding.top - padding.bottom} 
                fill="transparent" 
                className="cursor-pointer"
                onMouseEnter={() => setHoveredLap(lap)}
              />
            );
          })}
        </svg>
      </div>
    );
  };

  return (
    <div className="h-screen max-h-screen overflow-hidden f1-grid-bg text-slate-100 font-sans relative flex flex-col no-scrollbar select-none">
      
      {/* Dynamic ambient backlights matching selected team */}
      <div className="glow-orb" style={{ backgroundColor: activeLivery.primary, top: '-250px', left: '-250px' }} />
      <div className="glow-orb" style={{ backgroundColor: activeLivery.primary, bottom: '-250px', right: '-250px' }} />

      {/* 1. Racing Ticker (Top Banner) */}
      <div className="w-full bg-[#04060a] text-white border-b border-slate-900 py-1 px-4 text-[9px] font-mono tracking-widest uppercase flex items-center z-50 justify-between h-7 shrink-0">
        <div className="flex items-center gap-2 overflow-hidden w-2/3">
          <span className="text-red-500 font-bold animate-pulse">● TRACK MONITOR</span>
          <div className="animate-marquee whitespace-nowrap text-slate-300">
            CURRENT GRAND PRIX: {selectedCircuit.displayName.toUpperCase()} • DRS: ENABLED • LIVERY STATE: {activeLivery.name.toUpperCase()} ACTIVE • RADAR REPORT: CLOUD COVER 12% - PRECIPITATION PROBABILITY 0% FOR SESSION DURATION
          </div>
        </div>
        <div className="flex items-center gap-3 font-mono text-[9px]">
          <span className="text-slate-550">CONN_OK: <strong className="text-green-500 font-bold">100%</strong></span>
          <span className="text-slate-550">LATENCY: <strong className="text-green-500 font-bold">12ms</strong></span>
        </div>
      </div>

      {/* Main viewport frame */}
      <div className="flex-1 flex flex-col p-3 overflow-hidden gap-3 z-10">
        
        {/* Compact Title Row */}
        <header className="flex justify-between items-center bg-[#070b13]/60 border border-white/5 px-4 py-2 rounded-xl h-12 glass-panel shrink-0">
          <div className="flex items-center gap-2">
            <span className="bg-red-650 text-[8px] font-black tracking-widest px-1.5 py-0.5 rounded text-white italic font-telemetry">F1 ENGINE</span>
            <h1 className="text-base font-black italic tracking-tighter text-white font-display uppercase flex items-center gap-1.5">
              PIT-WALL TELEMETRY SYSTEM <span className="font-telemetry font-bold text-[10px]" style={{ color: activeLivery.primary }}>v2.6</span>
            </h1>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-4 text-[9px] font-mono text-slate-400">
            <span>SELECTED TEAM: <strong style={{ color: activeLivery.primary }}>{activeLivery.name.toUpperCase()}</strong></span>
            <div className="flex items-center gap-1.5 bg-slate-950/60 px-2 py-0.5 rounded border border-slate-800">
              <span className={`w-2 h-2 rounded-full ${apiOnline === null ? 'bg-amber-400' : apiOnline ? 'bg-green-500' : 'bg-red-500'} ${apiOnline ? 'animate-pulse shadow-[0_0_6px_rgba(34,197,94,0.6)]' : ''}`}></span>
              <span className={`font-bold uppercase text-[8px] ${apiOnline === null ? 'text-amber-400' : apiOnline ? 'text-green-400' : 'text-red-400'}`}>
                {apiOnline === null ? 'SYNCING LINK' : apiOnline ? 'SECURE CONNECT' : 'LINK OFFLINE'}
              </span>
            </div>
          </div>
        </header>

        {/* Dynamic Telemetry System Warning Alerts */}
        {error && (
          <div className="bg-red-950/40 border border-red-900/60 text-red-400 px-4 py-2 rounded-xl font-mono text-[9px] uppercase tracking-widest shrink-0">
            ⚠️ WARNING // SYSTEM DIAGNOSTIC ERROR REPORT // {error}
          </div>
        )}

        {/* 3-Column viewport layout */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 overflow-hidden">
          
          {/* COLUMN 1: 2026 LIVE DRIVER CHAMPIONSHIP STANDINGS (lg:col-span-3) */}
          <div className="lg:col-span-3 flex flex-col gap-3 overflow-hidden">
            <section className="bg-slate-950/40 border border-white/5 rounded-xl p-3 flex flex-col gap-3 glass-panel flex-1 overflow-hidden">
              <h2 className="text-[10px] font-black italic text-slate-200 tracking-wider uppercase font-display border-b border-slate-850 pb-1.5 flex justify-between items-center shrink-0">
                <span>🏆 2026 LIVE STANDINGS</span>
                <span className="text-[8px] font-mono text-green-455 animate-pulse font-black uppercase">● LIVE SYNC</span>
              </h2>

              {/* Scrollable Leaderboard */}
              <div className="flex-1 overflow-y-auto no-scrollbar pr-0.5 space-y-1.5">
                {standingsLoading && standings.length === 0 ? (
                  <div className="text-center font-mono text-[9px] text-slate-500 py-12 animate-pulse uppercase">
                    CONNECTING TO F1 RESULTS GATEWAY...
                  </div>
                ) : (
                  standings.map((driver) => {
                    const isCurrentDriver = activeLivery.name.toLowerCase().includes(driver.team.toLowerCase().split(' ')[0]) ||
                      (activeLivery.id === 'f1' && driver.position === '1');
                    
                    let teamBorderColor = 'rgba(255, 255, 255, 0.05)';
                    let teamLeftStripColor = 'bg-slate-800';

                    if (driver.team.toLowerCase().includes('mercedes')) {
                      teamLeftStripColor = 'bg-[#00ffc4]';
                      if (activeLivery.id === 'mercedes') teamBorderColor = '#00ffc440';
                    } else if (driver.team.toLowerCase().includes('ferrari')) {
                      teamLeftStripColor = 'bg-[#ff1801]';
                      if (activeLivery.id === 'ferrari') teamBorderColor = '#ff180140';
                    } else if (driver.team.toLowerCase().includes('red bull')) {
                      teamLeftStripColor = 'bg-[#facc15]';
                      if (activeLivery.id === 'redbull') teamBorderColor = '#facc1540';
                    } else if (driver.team.toLowerCase().includes('mclaren')) {
                      teamLeftStripColor = 'bg-[#ff8700]';
                      if (activeLivery.id === 'mclaren') teamBorderColor = '#ff870040';
                    } else if (driver.team.toLowerCase().includes('aston martin')) {
                      teamLeftStripColor = 'bg-[#c5e82a]';
                      if (activeLivery.id === 'aston') teamBorderColor = '#c5e82a40';
                    }

                    return (
                      <div 
                        key={driver.position}
                        className="flex items-center justify-between bg-[#04060c]/40 hover:bg-slate-900/50 border rounded-lg p-2 transition-all relative overflow-hidden h-11 shrink-0"
                        style={{
                          borderColor: teamBorderColor,
                          background: isCurrentDriver ? `${activeLivery.primary}08` : 'rgba(4,6,12,0.4)'
                        }}
                      >
                        {/* Team stripe on left */}
                        <div className={`absolute left-0 top-0 bottom-0 w-0.5 ${teamLeftStripColor}`} />
                        
                        <div className="flex items-center gap-2 pl-1.5 overflow-hidden">
                          <span className="font-telemetry font-bold text-[9px] text-slate-500 w-4 text-center">
                            {driver.position}
                          </span>
                          <div className="flex flex-col overflow-hidden">
                            <span className="text-[10px] font-black text-slate-200 truncate uppercase font-display">
                              {driver.name} <span className="font-telemetry font-normal text-[8px] text-slate-550">({driver.code})</span>
                            </span>
                            <span className="text-[7.5px] font-mono text-slate-500 truncate uppercase tracking-wide">
                              {driver.team}
                            </span>
                          </div>
                        </div>
                        
                        <div className="text-right shrink-0">
                          <span className="font-telemetry font-bold text-white text-[10px] tracking-wider">
                            {driver.points}
                          </span>
                          <span className="block text-[6px] font-mono text-slate-550 uppercase">
                            PTS
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Technical 2026 specs panel */}
              <div className="bg-slate-950/80 border border-slate-900 p-2.5 rounded-lg flex flex-col gap-1 shrink-0">
                <span className="text-[8px] font-mono text-slate-500 uppercase font-black block border-b border-slate-900 pb-1 mb-1 tracking-wider">
                  📊 2026 REGULATION CORRELATIONS
                </span>
                <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[8px] font-mono text-slate-400">
                  <div>PU OUTPUT: <span className="text-white font-bold">1025+ HP</span></div>
                  <div>BIOFUEL: <span className="text-white font-bold">E10 100% SUST.</span></div>
                  <div>ACTIVE AERO: <span className="text-white font-bold">Z-MODE ACTIVE</span></div>
                  <div>MIN WEIGHT: <span className="text-white font-bold">722 KG</span></div>
                </div>
              </div>
            </section>
          </div>

          {/* COLUMN 2: STRATEGY PLANNER WITH CIRCUIT & LIVERY ACCESS (lg:col-span-4) */}
          <div className="lg:col-span-4 flex flex-col gap-3 overflow-y-auto no-scrollbar">
            
            <section 
              className="bg-slate-950/40 border rounded-xl p-3.5 flex flex-col gap-3 flex-1 justify-between glass-panel"
              style={{ borderColor: `${activeLivery.primary}30` }}
            >
              <div>
                <h2 className="text-[10px] font-black italic text-slate-300 tracking-wider uppercase font-display border-b border-slate-850 pb-1.5 flex justify-between items-center mb-3">
                  <span>02 // STRATEGY CONTROL PANEL</span>
                  
                  {/* Start lights sequence */}
                  <div className="flex gap-1 items-center bg-slate-950/80 border border-slate-850 px-2 py-0.5 rounded-md">
                    {[1, 2, 3, 4, 5].map((light) => (
                      <span 
                        key={light} 
                        className={`w-2 h-2 rounded-full border border-slate-850 ${
                          loading 
                            ? 'bg-red-650 animate-pulse shadow-[0_0_6px_#ef4444]' 
                            : 'bg-red-950/40'
                        }`}
                      />
                    ))}
                    <span className="text-[6px] font-mono text-slate-500 ml-1">GRID</span>
                  </div>
                </h2>

                {/* Circuit select & layout outline */}
                <div className="grid grid-cols-12 gap-3 mb-3 shrink-0">
                  <div className="col-span-7 flex flex-col gap-2">
                    <span className="text-[8px] font-mono text-slate-550 uppercase block">TARGET CIRCUIT</span>
                    <select
                      value={selectedCircuit.id}
                      onChange={(e) => handleCircuitChange(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 text-slate-200 px-2 py-1.5 rounded-lg focus:outline-none focus:border-red-500 font-display text-xs font-bold"
                    >
                      {CIRCUITS.map((c) => (
                        <option key={c.id} value={c.id} className="bg-slate-950 text-slate-200">
                          {c.flag} {c.name} ({c.country})
                        </option>
                      ))}
                    </select>
                    
                    <div className="grid grid-cols-2 gap-2 mt-0.5">
                      <div className="bg-slate-950/60 p-1.5 rounded border border-slate-900 flex flex-col">
                        <span className="text-[6px] font-mono text-slate-500 uppercase">LENGTH</span>
                        <span className="text-[9px] font-telemetry font-bold text-white tracking-wide">{selectedCircuit.length}</span>
                      </div>
                      <div className="bg-slate-950/60 p-1.5 rounded border border-slate-900 flex flex-col">
                        <span className="text-[6px] font-mono text-slate-500 uppercase">RACE LAPS</span>
                        <span className="text-[9px] font-telemetry font-bold text-white tracking-wide">{selectedCircuit.laps}</span>
                      </div>
                    </div>
                  </div>

                  <div className="col-span-5 bg-slate-950/60 border border-slate-900 rounded-xl p-1.5 flex items-center justify-center relative overflow-hidden">
                    <svg viewBox="0 0 100 100" className="w-16 h-16 text-slate-800">
                      <path 
                        d={selectedCircuit.path} 
                        fill="none" 
                        stroke={activeLivery.primary} 
                        strokeWidth="4" 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        style={{ filter: `drop-shadow(0 0 4px ${activeLivery.primary})` }}
                      />
                    </svg>
                  </div>
                </div>

                {/* Horizontal Livery selector */}
                <div className="mb-3 shrink-0">
                  <span className="text-[8px] font-mono text-slate-550 uppercase block mb-1.5">ACTIVE TEAM LIVERY</span>
                  <div className="flex gap-1 overflow-x-auto no-scrollbar pb-1">
                    {LIVERIES.map((l) => (
                      <button
                        key={l.id}
                        onClick={() => setActiveLivery(l)}
                        className="relative overflow-hidden py-1 px-2.5 rounded-lg border flex items-center gap-1.5 transition-all cursor-pointer bg-slate-950/40 hover:bg-slate-900/60 shrink-0"
                        style={{
                          borderColor: activeLivery.id === l.id ? l.primary : 'rgba(255,255,255,0.05)',
                          boxShadow: activeLivery.id === l.id ? `0 0 8px ${l.glow}` : 'none'
                        }}
                      >
                        <span className="text-[9px]">{l.logo}</span>
                        <span className="text-[8px] font-black font-display tracking-wider text-slate-200 uppercase">{l.name.split(' ')[0]}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Presets */}
                <div className="mb-3">
                  <label className="block text-[8px] uppercase font-mono tracking-widest text-slate-550 mb-1.5">Preset Profiles</label>
                  <div className="grid grid-cols-4 gap-1">
                    <button onClick={() => loadPreset('1-stop-mh')} className="bg-slate-950 hover:bg-slate-850 text-[9px] font-bold text-slate-400 hover:text-white py-1.5 rounded transition-colors border border-slate-850 cursor-pointer">1-S M-H</button>
                    <button onClick={() => loadPreset('1-stop-sh')} className="bg-slate-950 hover:bg-slate-850 text-[9px] font-bold text-slate-400 hover:text-white py-1.5 rounded transition-colors border border-slate-850 cursor-pointer">1-S S-H</button>
                    <button onClick={() => loadPreset('2-stop-smm')} className="bg-slate-950 hover:bg-slate-850 text-[9px] font-bold text-slate-400 hover:text-white py-1.5 rounded transition-colors border border-slate-850 cursor-pointer">2-S SMM</button>
                    <button onClick={() => loadPreset('2-stop-mhm')} className="bg-slate-950 hover:bg-slate-850 text-[9px] font-bold text-slate-400 hover:text-white py-1.5 rounded transition-colors border border-slate-850 cursor-pointer">2-S MHM</button>
                  </div>
                </div>

                {/* Visual bar */}
                <div className="mb-4">
                  <div className="flex justify-between items-center text-[9px] font-mono text-slate-500 mb-1.5">
                    <span>LAPS ASSIGNED</span>
                    <span style={{ color: lapDifference === 0 ? '#10b981' : '#f87171' }} className="font-telemetry font-bold">
                      {totalStintLaps} / {selectedCircuit.laps} Laps
                    </span>
                  </div>
                  
                  <div className="w-full h-3 bg-slate-950 rounded-full border border-slate-850 overflow-hidden flex shadow-inner">
                    {stints.map((stint, idx) => {
                      const pct = (stint.laps / Math.max(1, selectedCircuit.laps)) * 100;
                      return (
                        <div
                          key={idx}
                          style={{ width: `${pct}%`, backgroundColor: getCompoundColor(stint.compound) }}
                          className="h-full border-r border-slate-950/20 last:border-0 hover:brightness-110"
                        />
                      );
                    })}
                  </div>

                  {lapDifference !== 0 && (
                    <div className="mt-2 text-[9px] font-mono p-1.5 bg-red-950/20 border border-red-900/40 rounded text-red-400">
                      ⚠️ Mismatch: {lapDifference > 0 ? `+${lapDifference} Laps excess.` : `${lapDifference} Laps missing.`}
                    </div>
                  )}
                </div>

                {/* Visual Stints List */}
                <div className="space-y-2 max-h-[170px] overflow-y-auto no-scrollbar pr-1">
                  {stints.map((stint, idx) => (
                    <div key={idx} className="bg-slate-950/60 border border-slate-850 rounded-lg p-2.5 relative flex items-center justify-between group hover:border-slate-700 transition-colors">
                      <div className="flex flex-col gap-1">
                        <span className="text-[8px] font-mono text-slate-500">STINT {idx + 1} TYRE</span>
                        <div className="flex gap-0.5">
                          {(['SOFT', 'MEDIUM', 'HARD'] as const).map((comp) => (
                            <button
                              key={comp}
                              onClick={() => updateStintCompound(idx, comp)}
                              className={`px-2 py-0.5 rounded text-[8px] font-black border transition-all cursor-pointer ${
                                stint.compound === comp
                                  ? getCompoundTailwindBg(comp)
                                  : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-300'
                              }`}
                            >
                              {comp.slice(0, 1)}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-1">
                        <span className="text-[8px] font-mono text-slate-500">STINT LAPS</span>
                        <div className="flex items-center gap-1.5">
                          <button onClick={() => updateStintLaps(idx, stint.laps - 1)} className="bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white w-5 h-5 rounded flex items-center justify-center font-bold text-[10px]">-</button>
                          <input
                            type="number"
                            value={stint.laps}
                            onChange={(e) => updateStintLaps(idx, parseInt(e.target.value) || 0)}
                            className="bg-slate-900 border border-slate-800 text-white w-8 py-0.5 rounded text-center text-[10px] font-telemetry font-bold"
                          />
                          <button onClick={() => updateStintLaps(idx, stint.laps + 1)} className="bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white w-5 h-5 rounded flex items-center justify-center font-bold text-[10px]">+</button>
                        </div>
                      </div>

                      {stints.length > 1 && (
                        <button onClick={() => removeStint(idx)} className="absolute -top-1 -right-1 bg-red-950 border border-red-900 text-red-500 hover:bg-red-900 hover:text-white w-4.5 h-4.5 rounded-full flex items-center justify-center text-[9px] transition-colors">✕</button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-3 flex flex-col gap-2">
                <button
                  onClick={addStint}
                  disabled={totalStintLaps >= selectedCircuit.laps}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider transition-colors disabled:opacity-40"
                >
                  + Add Segment
                </button>

                <button
                  onClick={runSimulation}
                  disabled={loading || lapDifference !== 0}
                  style={{
                    backgroundColor: loading ? '#1e293b' : isOutdated ? '#d97706' : activeLivery.primary,
                    color: activeLivery.secondary
                  }}
                  className={`w-full relative overflow-hidden py-3 rounded-lg text-white font-black tracking-widest text-[10px] uppercase shadow-lg transition-all cursor-pointer font-display ${isOutdated ? 'animate-pulse' : ''}`}
                >
                  {loading 
                    ? 'CALCULATING TELEMETRY CORRELATIONS...' 
                    : isOutdated 
                      ? '⚠️ SYNCHRONIZE TELEMETRY DATA' 
                      : 'RUN STRATEGY SIMULATOR'
                  }
                </button>
              </div>
            </section>
          </div>

          {/* COLUMN 3: TELEMETRY VIEWPORTS & TIMINGS (lg:col-span-5) */}
          <div className="lg:col-span-5 flex flex-col gap-3 overflow-hidden">
            
            {/* High-Tech Tab Switcher */}
            <div className="flex bg-slate-955/60 border border-slate-850 p-1 rounded-xl h-11 shrink-0 glass-panel">
              <button
                onClick={() => setActiveTab('telemetry')}
                className={`flex-1 rounded-lg text-xs font-black font-display uppercase tracking-wider transition-all cursor-pointer ${
                  activeTab === 'telemetry'
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-500 hover:text-slate-350'
                }`}
                style={activeTab === 'telemetry' ? { borderBottom: `2px solid ${activeLivery.primary}` } : {}}
              >
                📊 LIVE TELEMETRY VIEW
              </button>
              <button
                onClick={() => setActiveTab('qa')}
                className={`flex-1 rounded-lg text-xs font-black font-display uppercase tracking-wider transition-all cursor-pointer ${
                  activeTab === 'qa'
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-500 hover:text-slate-355'
                }`}
                style={activeTab === 'qa' ? { borderBottom: `2px solid ${activeLivery.primary}` } : {}}
              >
                🤖 GP KNOWLEDGE ASSISTANT (RAG)
              </button>
            </div>

            {/* TAB CONTENTS */}
            {activeTab === 'telemetry' ? (
              results && !loading ? (
                <div className="flex-1 flex flex-col gap-3 overflow-hidden">
                  
                  {/* HUD Sector Timing Card */}
                  {hoveredLap && (
                    <section 
                      className="bg-slate-950/40 border border-slate-850 rounded-xl p-3 flex justify-between items-center shadow-md relative glass-panel"
                      style={{ borderColor: isOutdated ? '#d9770660' : 'rgba(30, 41, 59, 0.5)' }}
                    >
                      {isOutdated && (
                        <span className="absolute top-1 right-2 text-[7px] font-mono text-amber-500 animate-pulse font-black uppercase">
                          [ TELEMETRY DISPLAY CACHED // OUT OF SYNC ]
                        </span>
                      )}
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[8px] font-mono text-slate-550 uppercase">CURRENT FOCUS LAP</span>
                        <span className="text-sm font-bold font-telemetry text-white">
                          LAP {hoveredLap.overall_lap} <span className="text-[9px] font-normal font-display text-slate-455">({hoveredLap.compound})</span>
                        </span>
                      </div>
                      
                      {/* 3 Sectors HUD */}
                      <div className="flex gap-4">
                        {getSectorStats(hoveredLap).map((sec, idx) => (
                          <div key={idx} className="flex flex-col items-center">
                            <span className="text-[8px] font-mono text-slate-555">{sec.name}</span>
                            <span className={`font-telemetry text-[11px] font-black tracking-wide ${sec.color}`}>{sec.val}s</span>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}

                  {/* Telemetry degradation curve */}
                  {renderTelemetryChart()}

                  {/* Stint timing table - fills remaining space */}
                  <div className="flex-1 overflow-y-auto no-scrollbar border border-slate-850 rounded-xl bg-slate-950/40 glass-panel">
                    <StintTable results={results} />
                  </div>

                </div>
              ) : (
                /* Awaiting screen */
                <div className="flex-1 bg-slate-955/20 border border-slate-850 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center select-none glass-panel">
                  <svg className="w-12 h-12 mb-4 text-slate-800 animate-pulse" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <circle cx="50" cy="50" r="40" strokeDasharray="3 3"/>
                    <circle cx="50" cy="50" r="28" />
                    <path d="M 50 15 L 50 85 M 15 50 L 85 50" />
                  </svg>
                  <h3 className="text-sm font-bold font-display italic tracking-wide uppercase text-slate-400">Awaiting Simulation Results</h3>
                  <p className="text-[10px] text-slate-650 font-mono mt-1.5 max-w-xs">
                    Set target track and tyres stint segments in race planner panel and compile Strategy to view performance telemetry graphs.
                  </p>
                </div>
              )
            ) : (
              /* Q&A ASSISTANT (RAG) INTERFACE */
              <div className="flex-1 flex flex-col gap-3 overflow-hidden">
                
                {/* 1. URL Ingest Form */}
                <form onSubmit={handleIngest} className="bg-slate-955/40 border border-slate-850 rounded-xl p-3 flex flex-col gap-2 shrink-0 glass-panel">
                  <span className="text-[8px] font-mono text-slate-550 uppercase block">Ingest New F1 Source (Wikipedia or F1 Website URL)</span>
                  <div className="flex gap-2">
                    <input 
                      type="url" 
                      placeholder="https://en.wikipedia.org/wiki/2026_Formula_One_World_Championship" 
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      className="flex-1 bg-slate-950 border border-slate-850 text-[10px] text-white px-2.5 py-1.5 rounded-lg outline-none focus:border-slate-700 font-mono"
                      disabled={ingesting}
                    />
                    <button 
                      type="submit" 
                      className="bg-slate-950 border border-slate-850 hover:border-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-lg text-[9px] font-mono font-bold uppercase transition-colors cursor-pointer shrink-0 disabled:opacity-50"
                      disabled={ingesting}
                    >
                      {ingesting ? 'INGESTING...' : 'INGEST URL'}
                    </button>
                  </div>
                  {ingestStatus && (
                    <div className="text-[8px] font-mono text-slate-400 tracking-wider">
                      {ingestStatus}
                    </div>
                  )}
                </form>

                {/* 2. Chat history box - fills remaining space */}
                <div className="flex-1 overflow-y-auto no-scrollbar border border-slate-850 bg-slate-955/30 rounded-xl p-3 space-y-3 font-mono text-[10px] glass-panel">
                  {chatHistory.map((msg, idx) => (
                    <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className="text-[8px] text-slate-550 uppercase tracking-widest mb-0.5">
                        {msg.role === 'user' ? '// STRATEGIST QUERY' : `// DECISION SUPPORT [${activeLivery.name.toUpperCase()}]`}
                      </div>
                      <div 
                        className="p-2.5 rounded-lg max-w-[95%] border break-words relative overflow-hidden"
                        style={{
                          backgroundColor: msg.role === 'user' ? 'rgba(15, 23, 42, 0.45)' : 'rgba(4, 6, 11, 0.45)',
                          borderColor: msg.role === 'user' ? 'rgba(30, 41, 59, 0.5)' : `${activeLivery.primary}30`,
                        }}
                      >
                        {msg.role !== 'user' && (
                          <div className="absolute left-0 top-0 bottom-0 w-1" style={{ backgroundColor: activeLivery.primary }} />
                        )}
                        <span className="leading-relaxed text-slate-200">{msg.text}</span>
                        
                        {/* Sources list */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-2 pt-1.5 border-t border-slate-850/40 text-[8px] text-slate-550 flex flex-wrap gap-1.5">
                            <span className="font-bold">SOURCES:</span>
                            {msg.sources.map((src, i) => (
                              <span key={i} className="bg-slate-900/60 px-1 py-0.5 rounded border border-slate-850 truncate max-w-[140px]" title={src}>
                                {src.includes('/') ? src.split('/').pop() : src}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {submittingQa && (
                    <div className="flex flex-col items-start animate-pulse">
                      <span className="text-[8px] text-slate-500 uppercase tracking-widest mb-0.5">// THINKING</span>
                      <div className="p-2 rounded-lg bg-slate-950/40 border border-slate-850 text-slate-400 italic">
                        CONSULTING RAG INDEXES AND VERIFYING DATA Gaps...
                      </div>
                    </div>
                  )}
                </div>

                {/* 3. QA Prompt Input form */}
                <form onSubmit={handleQaSubmit} className="bg-slate-955/40 border border-slate-850 px-3 py-2 rounded-xl flex items-center justify-between shrink-0 glass-panel">
                  <input 
                    type="text" 
                    placeholder="Ask strategist (e.g. Pit speed limits? / Drivers wins? / Weather rules?)" 
                    value={qaInput}
                    onChange={(e) => setQaInput(e.target.value)}
                    className="flex-1 bg-transparent border-0 outline-none text-[10px] text-white font-mono placeholder-slate-650 mr-2"
                    disabled={submittingQa}
                  />
                  <button 
                    type="submit" 
                    className="text-[9px] font-mono font-bold text-white px-3.5 py-1 rounded-lg transition-colors cursor-pointer shrink-0"
                    style={{ backgroundColor: activeLivery.primary }}
                    disabled={submittingQa}
                  >
                    QUERY
                  </button>
                </form>

              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}