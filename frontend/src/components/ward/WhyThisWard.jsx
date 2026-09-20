import React from 'react';
import { 
  Sparkles, 
  AlertCircle, 
  TrendingUp, 
  CheckCircle2, 
  HelpCircle,
  Activity,
  Layers,
  Sliders,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import { Badge } from '../common/Badge';
import { formatStressScore, getStressBandStyle } from '../../utils/formatters';

export const WhyThisWard = ({ wardData, explanationData, anomalyData }) => {
  if (!wardData) return null;

  const wardCode = wardData.ward_code;
  const urbanStress = wardData.urban_stress !== null && wardData.urban_stress !== undefined ? Number(wardData.urban_stress) : null;
  const stressBandLabel = wardData.stress_band || 'Moderate';
  const stressBandStyle = getStressBandStyle(stressBandLabel);

  // Extract explanation fields from authoritative dataset
  const exp = explanationData || {};
  const topDomain1 = exp.top_domain_1 || 'sanitation';
  const topDomain2 = exp.top_domain_2 || 'green_space';
  const topDomain3 = exp.top_domain_3 || 'safety';
  const clusterName = exp.cluster || wardData.cluster || 'Cluster';
  const isAnomaly = !!(exp.anomaly_candidate || wardData.anomaly_candidate);
  const anomalyMse = exp.anomaly_score !== null && exp.anomaly_score !== undefined 
    ? Number(exp.anomaly_score).toFixed(3) 
    : (wardData.reconstruction_mse !== null && wardData.reconstruction_mse !== undefined ? Number(wardData.reconstruction_mse).toFixed(3) : 'No data');
  const bestScenario = exp.best_scenario || wardData.best_scenario || 'healthcare_capacity_plus_20';
  const bestScenarioDelta = exp.best_scenario_change !== null && exp.best_scenario_change !== undefined 
    ? Number(exp.best_scenario_change).toFixed(2) 
    : (wardData.best_scenario_change !== null && wardData.best_scenario_change !== undefined ? Number(wardData.best_scenario_change).toFixed(2) : 'No data');

  return (
    <div className="p-3.5 rounded-xl bg-slate-900/80 border border-cyan-500/20 shadow-xl space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
              Why This Ward?
            </h4>
            <span className="text-[10px] text-slate-400 font-mono">Evidence-Based Analytical Rationale</span>
          </div>
        </div>
        <Badge variant="model" size="xs">Civic AI Model</Badge>
      </div>

      {/* 1. Relative Urban Pressure Band */}
      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-white/5 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-medium text-slate-300">Relative Urban Pressure</span>
            <Badge variant="derived" size="xs">Percentile Index</Badge>
          </div>
          <span className="text-[10px] text-slate-400">
            Percentile-based analytical index across 24 BMC wards (non-governmental)
          </span>
        </div>
        <div className="text-right">
          <span className="text-base font-bold font-mono text-white">
            {formatStressScore(urbanStress)}
          </span>
          <div className="text-[10px] font-semibold" style={{ color: stressBandStyle.color }}>
            {stressBandLabel}
          </div>
        </div>
      </div>

      {/* 2. Strongest Pressure Domains */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider font-mono">
            Main Pressure Domains
          </span>
          <Badge variant="derived" size="xs">Ranked Drivers</Badge>
        </div>
        <div className="grid grid-cols-3 gap-1.5 font-mono text-[11px]">
          <div className="p-1.5 rounded bg-rose-950/30 border border-rose-500/20 text-rose-300 text-center capitalize">
            1. {topDomain1.replace('_', ' ')}
          </div>
          <div className="p-1.5 rounded bg-amber-950/30 border border-amber-500/20 text-amber-300 text-center capitalize">
            2. {topDomain2.replace('_', ' ')}
          </div>
          <div className="p-1.5 rounded bg-yellow-950/30 border border-yellow-500/20 text-yellow-300 text-center capitalize">
            3. {topDomain3.replace('_', ' ')}
          </div>
        </div>
      </div>

      {/* 3. Supporting Evidence Indicators */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider font-mono">
            Key Supporting Evidence
          </span>
          <Badge variant="observed" size="xs">Observed GIS</Badge>
        </div>
        <div className="space-y-1 text-xs font-mono">
          <div className="flex items-center justify-between p-1.5 rounded bg-slate-950/40 border border-white/5">
            <span className="text-slate-400">Population (2011 Census)</span>
            <span className="text-slate-200 font-bold">
              {wardData.population_2011 ? Number(wardData.population_2011).toLocaleString('en-IN') : 'No data'}
            </span>
          </div>
          <div className="flex items-center justify-between p-1.5 rounded bg-slate-950/40 border border-white/5">
            <span className="text-slate-400">Public Toilets per 10k Pop</span>
            <span className="text-slate-200 font-bold">
              {wardData.population_2011 && wardData.functional_toilets_total 
                ? (Number(wardData.functional_toilets_total) / (Number(wardData.population_2011) / 10000)).toFixed(1) 
                : (wardData.sanitation_stress !== null && wardData.sanitation_stress !== undefined ? `${Number(wardData.sanitation_stress).toFixed(1)}%` : 'No data')}
            </span>
          </div>
          <div className="flex items-center justify-between p-1.5 rounded bg-slate-950/40 border border-white/5">
            <span className="text-slate-400">2024 CCRS Civic Complaints</span>
            <span className="text-slate-200 font-bold">
              {wardData.complaints_received_2024 !== null && wardData.complaints_received_2024 !== undefined 
                ? Number(wardData.complaints_received_2024).toLocaleString('en-IN') 
                : 'No data'}
            </span>
          </div>
        </div>
      </div>

      {/* 4. AI Typology & Anomaly Signal */}
      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-purple-500/20 space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-purple-300 font-mono uppercase">AI Model Diagnostics</span>
          <Badge variant="model" size="xs">Deep Learning</Badge>
        </div>
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400">Spatial Latent Cluster:</span>
          <span className="text-purple-300 font-bold">{clusterName.replace('_', ' ')}</span>
        </div>
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400">Reconstruction Anomaly:</span>
          {isAnomaly ? (
            <span className="text-rose-400 font-bold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Candidate (MSE: {anomalyMse})
            </span>
          ) : (
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Standard (MSE: {anomalyMse})
            </span>
          )}
        </div>
        {isAnomaly && (
          <p className="text-[10px] text-rose-300/80 font-sans mt-1 bg-rose-950/40 p-1.5 rounded border border-rose-500/20">
            Model-derived anomaly signal, not a diagnosis or proof of a real-world problem.
          </p>
        )}
      </div>

      {/* 5. Best Modeled Intervention Scenario */}
      <div className="p-2.5 rounded-lg bg-slate-950/60 border border-emerald-500/20 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-emerald-400 font-mono uppercase">Optimal Modeled Scenario</span>
          <Badge variant="scenario" size="xs">Simulation</Badge>
        </div>
        <div className="text-xs font-medium text-slate-200 capitalize">
          {bestScenario.replace(/_/g, ' ')}
        </div>
        <div className="flex items-center justify-between text-xs font-mono pt-1">
          <span className="text-slate-400">Modeled Relative-Pressure Change:</span>
          <span className="text-emerald-400 font-bold">{bestScenarioDelta} pts</span>
        </div>
      </div>
    </div>
  );
};
