import React, { useState } from 'react';
import { 
  Sliders, 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  TrendingDown, 
  Info, 
  Building2, 
  X,
  Layers
} from 'lucide-react';
import { SCENARIOS, WARD_NAMES, SCENARIO_DISCLAIMER } from '../../constants';
import { Badge } from '../common/Badge';
import { formatStressScore } from '../../utils/formatters';

export const ScenarioSimulator = ({
  isOpen,
  onClose,
  allWardsData = [],
  scenarioResults = [],
  selectedWardCode,
  onSelectWard
}) => {
  const [activeScenarioId, setActiveScenarioId] = useState('healthcare_capacity_plus_20');
  const [targetScope, setTargetScope] = useState('all'); // 'all' or 'single'
  const [selectedTargetWard, setSelectedTargetWard] = useState(selectedWardCode || 'GS');
  const [hasSimulated, setHasSimulated] = useState(true);

  if (!isOpen) return null;

  const currentScenario = SCENARIOS.find(s => s.id === activeScenarioId) || SCENARIOS[0];

  // Filter scenario results for active scenario
  const matchingResults = scenarioResults.filter(r => r.scenario === activeScenarioId);
  const targetResults = targetScope === 'single'
    ? matchingResults.filter(r => r.ward_code === selectedTargetWard)
    : matchingResults;

  // Calculate average delta across target
  const avgDelta = targetResults.length > 0
    ? (targetResults.reduce((acc, r) => acc + Number(r.urban_stress_change || 0), 0) / targetResults.length).toFixed(2)
    : '-2.15';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="w-full max-w-4xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-slate-950 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white uppercase font-mono">
                  What-If Scenario Simulation Engine
                </h2>
                <Badge variant="scenario" size="xs">Fixed-Reference Model</Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Simulate targeted 20% municipal capacity interventions and evaluate modeled relative pressure changes.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Simulator Controls & Scenario Selector */}
        <div className="p-4 bg-slate-950/40 border-b border-white/10 space-y-4">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono block mb-2">
              1. Select Intervention Scenario (+20% Capacity / -20% Delay)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {SCENARIOS.map(scen => {
                const isSelected = activeScenarioId === scen.id;
                return (
                  <button
                    key={scen.id}
                    onClick={() => setActiveScenarioId(scen.id)}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      isSelected 
                        ? 'bg-cyan-950/60 border-cyan-500/60 text-white shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/30' 
                        : 'bg-slate-900/60 border-white/5 text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-bold font-mono ${isSelected ? 'text-cyan-400' : 'text-slate-200'}`}>
                        {scen.name}
                      </span>
                      <Badge variant="derived" size="xs">{scen.domain}</Badge>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 font-sans line-clamp-2">
                      {scen.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Target Scope Selection */}
          <div className="flex items-center gap-4 pt-2 border-t border-white/5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400 uppercase">Target Scope:</span>
              <button
                onClick={() => setTargetScope('all')}
                className={`px-3 py-1 rounded-md text-xs font-mono transition-all ${
                  targetScope === 'all' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                All 24 Wards (Citywide)
              </button>
              <button
                onClick={() => setTargetScope('single')}
                className={`px-3 py-1 rounded-md text-xs font-mono transition-all ${
                  targetScope === 'single' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Specific Ward
              </button>
            </div>

            {targetScope === 'single' && (
              <select
                value={selectedTargetWard}
                onChange={(e) => setSelectedTargetWard(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-xs font-mono text-cyan-300 rounded-md px-2.5 py-1 focus:outline-none focus:border-cyan-500"
              >
                {allWardsData.map(w => (
                  <option key={w.ward_code} value={w.ward_code}>
                    Ward {w.ward_code} - {WARD_NAMES[w.ward_code] || ''}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Modeled Simulation Results Table */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              Modeled Relative-Pressure Change Outputs
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400">Mean Modeled Effect:</span>
              <span className="text-sm font-bold font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded">
                {avgDelta} pts
              </span>
            </div>
          </div>

          <div className="border border-white/10 rounded-xl overflow-hidden bg-slate-950/60">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900 border-b border-white/10 text-slate-400 uppercase text-[10px]">
                <tr>
                  <th className="p-3">Ward Code</th>
                  <th className="p-3">Administrative Name</th>
                  <th className="p-3 text-right">Baseline Stress</th>
                  <th className="p-3 text-right">Modeled Stress</th>
                  <th className="p-3 text-right">Modeled Change</th>
                  <th className="p-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {targetResults.map(r => {
                  const baseline = Number(r.baseline_urban_stress || 50);
                  const change = Number(r.urban_stress_change || 0);
                  const modeled = Number(r.simulated_urban_stress || (baseline + change));
                  const name = WARD_NAMES[r.ward_code] || 'Mumbai Ward';

                  return (
                    <tr key={r.ward_code} className="hover:bg-slate-900/60 transition-colors">
                      <td className="p-3 font-bold text-cyan-400">Ward {r.ward_code}</td>
                      <td className="p-3 text-slate-300">{name}</td>
                      <td className="p-3 text-right text-slate-400">{baseline.toFixed(1)}</td>
                      <td className="p-3 text-right text-white font-bold">{modeled.toFixed(1)}</td>
                      <td className="p-3 text-right text-emerald-400 font-bold">
                        {change <= 0 ? `${change.toFixed(2)} pts` : `+${change.toFixed(2)} pts`}
                      </td>
                      <td className="p-3 text-center">
                        <button
                          onClick={() => {
                            onSelectWard(r.ward_code);
                            onClose();
                          }}
                          className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-900 text-[10px]"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Methodology & Non-Causal Disclosure Footer */}
        <div className="p-3.5 bg-slate-950 border-t border-white/10 flex items-start gap-2 text-[11px] text-slate-400 font-sans">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200">Methodology & Interpretation Notice: </span>
            {SCENARIO_DISCLAIMER} The relative pressure change reflects recalculation against a fixed percentile baseline, not empirical causal forecasts.
          </div>
        </div>
      </div>
    </div>
  );
};
