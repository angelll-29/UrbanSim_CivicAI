import React, { useState } from 'react';
import { 
  Building2, 
  Activity, 
  Sparkles, 
  AlertTriangle, 
  Network, 
  MessageSquare, 
  Layers, 
  Sliders, 
  ChevronRight,
  TrendingUp,
  BarChart3,
  CheckCircle2,
  GitCompare
} from 'lucide-react';
import { WARD_NAMES, DOMAINS, STRESS_BANDS, CLUSTER_COLORS } from '../../constants';
import { Badge } from '../common/Badge';
import { KPICard } from '../common/KPICard';
import { WardDetailPanel } from '../ward/WardDetailPanel';
import { formatNumber, formatStressScore, getStressColor, getStressBand } from '../../utils/formatters';

export const RightIntelligencePanel = ({
  selectedWardCode,
  onSelectWard,
  onCloseWard,
  allWardsData = [],
  wardBaseMap = {},
  explanationsMap = {},
  anomaliesMap = {},
  envProfilesMap = {},
  comparedWards = [],
  onAddToComparison,
  onOpenComparison,
  onOpenScenarioMode
}) => {
  // If a specific ward is selected, show the full Ward Detail Panel
  if (selectedWardCode) {
    const wardData = wardBaseMap[selectedWardCode] || allWardsData.find(w => w.ward_code === selectedWardCode) || {};
    const explanationData = explanationsMap[selectedWardCode] || {};
    const anomalyData = anomaliesMap[selectedWardCode] || {};
    const envProfileData = envProfilesMap[selectedWardCode] || {};
    const isCompared = comparedWards.includes(selectedWardCode);

    return (
      <aside className="w-96 h-[calc(100vh-3.5rem)] glass-panel border-l border-white/10 z-20 flex flex-col shadow-2xl">
        <WardDetailPanel
          wardData={wardData}
          explanationData={explanationData}
          anomalyData={anomalyData}
          envProfileData={envProfileData}
          onClose={onCloseWard}
          onAddToComparison={onAddToComparison}
          isCompared={isCompared}
        />
      </aside>
    );
  }

  // DEFAULT VIEW: Mumbai City-Wide Urban Intelligence Overview
  const validStresses = allWardsData
    .map(w => w.urban_stress)
    .filter(s => s !== null && s !== undefined && !isNaN(s));

  const avgStress = validStresses.length > 0 
    ? (validStresses.reduce((acc, s) => acc + Number(s), 0) / validStresses.length).toFixed(1)
    : '50.8';

  const anomalyCandidates = allWardsData.filter(w => w.anomaly_candidate);

  return (
    <aside className="w-96 h-[calc(100vh-3.5rem)] glass-panel border-l border-white/10 z-20 flex flex-col shadow-2xl overflow-hidden">
      {/* Panel Header */}
      <div className="p-4 border-b border-white/10 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-wider text-white uppercase font-mono">
                Mumbai Intelligence
              </h2>
              <span className="text-[11px] text-slate-400 font-mono">24 BMC Administrative Wards</span>
            </div>
          </div>
          <Badge variant="primary" size="xs">City Command</Badge>
        </div>

        {/* Citywide Key Indicator Strip */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <KPICard
            label="Mean Relative Pressure"
            value={avgStress}
            sublabel="Percentile index across 24 BMC wards"
            icon={Activity}
            color="cyan"
          />
          <KPICard
            label="AI Anomaly Signals"
            value={`${anomalyCandidates.length} Wards`}
            sublabel="ME, D, C Candidates"
            icon={AlertTriangle}
            color="rose"
          />
        </div>
      </div>

      {/* Scrollable Overview Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Quick Scenario & Compare Action Banners */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onOpenScenarioMode}
            className="p-2.5 rounded-lg bg-slate-900/80 border border-cyan-500/30 hover:border-cyan-500 hover:bg-slate-800/90 text-left transition-all group"
          >
            <div className="flex items-center justify-between text-cyan-400 mb-1">
              <Sliders className="w-4 h-4" />
              <ChevronRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
            </div>
            <span className="text-xs font-bold text-white block font-mono">What-If Scenarios</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Simulate 20% Capacity</span>
          </button>

          <button
            onClick={onOpenComparison}
            className="p-2.5 rounded-lg bg-slate-900/80 border border-purple-500/30 hover:border-purple-500 hover:bg-slate-800/90 text-left transition-all group"
          >
            <div className="flex items-center justify-between text-purple-400 mb-1">
              <GitCompare className="w-4 h-4" />
              <ChevronRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
            </div>
            <span className="text-xs font-bold text-white block font-mono">Ward Comparison</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Compare Up to 3 Wards</span>
          </button>
        </div>

        {/* AI Spatial Typologies / Clusters Summary */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-white/10 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-purple-400" />
              AI Latent Spatial Typology
            </span>
            <Badge variant="model" size="xs">4 Clusters</Badge>
          </div>

          <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
            Deep Autoencoder latent representation of infrastructure indicators clustered into 4 structural groups.
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
            <div className="p-2 rounded bg-slate-950/60 border border-sky-500/20">
              <div className="flex items-center gap-1.5 text-sky-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                Cluster 1 (12 Wards)
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block font-sans">Moderate mixed suburban infrastructure balance.</span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-purple-500/20">
              <div className="flex items-center gap-1.5 text-purple-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                Cluster 2 (6 Wards)
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block font-sans">High-density core with elevated sanitation stress.</span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-amber-500/20">
              <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                Cluster 3 (5 Wards)
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block font-sans">Large suburban footprint with transit dependencies.</span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-pink-500/20">
              <div className="flex items-center gap-1.5 text-pink-400 font-bold">
                <span className="w-2 h-2 rounded-full bg-pink-400"></span>
                Cluster 4 (1 Ward)
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block font-sans">Distinctive single-ward outlier typology.</span>
            </div>
          </div>
        </div>

        {/* 24 Wards Relative Pressure List */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-white/10 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              24 BMC Wards Overview
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Click to Inspect</span>
          </div>

          <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
            {allWardsData.map(ward => {
              const code = ward.ward_code;
              const name = WARD_NAMES[code] || 'Mumbai Ward';
              const stress = ward.urban_stress !== null && ward.urban_stress !== undefined ? Number(ward.urban_stress) : null;
              const color = stress !== null ? getStressColor(stress, ward.stress_band) : '#64748b';
              const isAnomaly = !!ward.anomaly_candidate;

              return (
                <button
                  key={code}
                  onClick={() => onSelectWard(code)}
                  className="w-full text-left p-2 rounded-lg bg-slate-950/40 hover:bg-slate-800/80 border border-white/5 hover:border-cyan-500/40 flex items-center justify-between text-xs transition-all group"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }}></span>
                    <span className="font-mono font-bold text-cyan-400 shrink-0">Ward {code}</span>
                    <span className="text-slate-300 truncate text-[11px]">{name}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 font-mono">
                    {isAnomaly && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-rose-950 text-rose-400 border border-rose-500/30">
                        Anomaly
                      </span>
                    )}
                    <span className="font-bold" style={{ color }}>{formatStressScore(stress)}</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition-colors" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
};
