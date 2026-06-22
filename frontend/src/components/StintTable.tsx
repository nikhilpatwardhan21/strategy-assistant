// import React from 'react';  //type:ignore

// Helper function to color-code the tire compounds
const getTireBadge = (compound: string) => {
  if (compound === 'SOFT') return 'bg-red-600 text-white';
  if (compound === 'MEDIUM') return 'bg-yellow-400 text-black';
  if (compound === 'HARD') return 'bg-white text-black';
  return 'bg-slate-700 text-white';
};

export default function StintTable({ results }: { results: any }) {
  if (!results) return null; // Don't show the table until simulation runs

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden max-w-4xl mx-auto mb-12">
      <div className="bg-red-600 px-4 py-2 font-bold text-white tracking-widest uppercase flex justify-between">
        <span>Stint Telemetry Breakdown</span>
        <span className="text-red-200">{results.circuit}</span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-300 font-mono">
          <thead className="text-xs text-gray-400 uppercase bg-gray-800 border-b border-gray-700">
            <tr>
              <th className="px-4 py-3">Stint</th>
              <th className="px-4 py-3 text-center">Compound</th>
              <th className="px-4 py-3 text-right">Lap Window</th>
              <th className="px-4 py-3 text-right">Avg Pace</th>
              <th className="px-4 py-3 text-right">Tire Drop</th>
              <th className="px-4 py-3 text-right text-white font-bold">Pit Loss</th>
            </tr>
          </thead>
          <tbody>
            {results.stints.map((stint: any) => (
              <tr key={stint.stint_number} className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
                <td className="px-4 py-3 font-bold text-white">0{stint.stint_number}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center justify-center w-8 h-6 rounded font-bold text-xs ${getTireBadge(stint.compound)}`}>
                    {stint.compound.charAt(0)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-bold text-slate-300">Laps {stint.lap_range}</td>
                <td className="px-4 py-3 text-right font-bold text-purple-400">{stint.avg_pace}</td>
                <td className="px-4 py-3 text-right font-bold text-amber-500">{stint.tire_drop}</td>
                <td className="px-4 py-3 text-right font-bold text-red-400 bg-gray-800/50">
                  {stint.pit_loss > 0 ? `+${stint.pit_loss}s` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}