interface StintTableProps {
  results: {
    circuit: string;
    stints: Array<{
      stint_number: number;
      compound: string;
      lap_range: string;
      avg_pace: string;
      tire_drop: string;
      pit_loss: number;
    }>;
  } | null;
}

const getTireCircleStyles = (compound: string) => {
  if (compound === 'SOFT') {
    return 'border-red-500 text-red-500 bg-red-950/40 shadow-[0_0_8px_rgba(239,68,68,0.4)]';
  }
  if (compound === 'MEDIUM') {
    return 'border-yellow-500 text-yellow-500 bg-yellow-950/40 shadow-[0_0_8px_rgba(234,179,8,0.4)]';
  }
  if (compound === 'HARD') {
    return 'border-white text-white bg-slate-900/60 shadow-[0_0_8px_rgba(255,255,255,0.2)]';
  }
  return 'border-slate-500 text-slate-400 bg-slate-950';
};

export default function StintTable({ results }: StintTableProps) {
  if (!results) return null;

  return (
    <div className="bg-slate-950/80 border border-slate-850 rounded-xl overflow-hidden shadow-2xl max-w-full mx-auto">
      
      {/* Table Header Accent */}
      <div className="bg-slate-900/80 px-4 py-3 border-b border-slate-850 flex justify-between items-center font-display tracking-wider">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-3.5 bg-red-600 rounded-sm animate-pulse"></span>
          <span className="text-[10px] font-black uppercase text-slate-200 font-display tracking-widest">STINT TELEMETRY REGISTER</span>
        </div>
        <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">
          SYS: {results.circuit} // CALIBRATED
        </span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left font-mono">
          <thead className="text-[9px] text-slate-500 uppercase bg-slate-950/60 border-b border-slate-850 font-display tracking-wider">
            <tr>
              <th className="px-4 py-2.5">STINT</th>
              <th className="px-4 py-2.5 text-center">COMPOUND</th>
              <th className="px-4 py-2.5 text-right font-display">LAP WINDOW</th>
              <th className="px-4 py-2.5 text-right font-display">AVG PACE</th>
              <th className="px-4 py-2.5 text-right font-display">TIRE DROP</th>
              <th className="px-4 py-2.5 text-right text-slate-450 font-display">PIT LOSS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850/30">
            {results.stints.map((stint) => (
              <tr 
                key={stint.stint_number} 
                className="hover:bg-slate-900/40 transition-colors"
              >
                <td className="px-4 py-3 font-telemetry font-bold text-white text-[11px]">
                  #{stint.stint_number}
                </td>
                <td className="px-4 py-3 flex justify-center">
                  <div className="flex items-center gap-2 w-24">
                    <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center font-telemetry font-black text-[9px] shrink-0 ${getTireCircleStyles(stint.compound)}`}>
                      {stint.compound.slice(0, 1)}
                    </span>
                    <span className="text-[9px] font-black font-display tracking-wider text-slate-300">{stint.compound}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-bold text-slate-300 text-[10px]">
                  LAPS {stint.lap_range}
                </td>
                <td className="px-4 py-3 text-right font-telemetry font-bold text-green-400 text-[10px] tracking-wide">
                  {stint.avg_pace}
                </td>
                <td className="px-4 py-3 text-right font-telemetry font-bold text-yellow-450 text-[10px] tracking-wide">
                  {stint.tire_drop}
                </td>
                <td className="px-4 py-3 text-right font-telemetry font-bold text-red-400 bg-red-950/5 text-[10px]">
                  {stint.pit_loss > 0 ? `+${stint.pit_loss}s` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}