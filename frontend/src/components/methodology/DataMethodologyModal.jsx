import React from 'react';
import { 
  Info, 
  X, 
  ShieldCheck, 
  Database, 
  Cpu, 
  Layers, 
  Activity, 
  Sliders, 
  Wind,
  CheckCircle2
} from 'lucide-react';
import { METHODOLOGY_NOTE, SCENARIO_DISCLAIMER } from '../../constants';
import { Badge } from '../common/Badge';

export const DataMethodologyModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
      <div className="w-full max-w-4xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-slate-950 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Info className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white uppercase font-mono">
                  Data Architecture & Methodology
                </h2>
                <Badge variant="primary" size="xs">Audit & Transparency</Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Mathematical formulations, data provenance, AI architecture, and operational assumptions.
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

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-slate-300 text-xs leading-relaxed font-sans">
          {/* 1. Urban Stress V2 Core Framework */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-cyan-500/30 space-y-2.5">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white font-mono uppercase">
                1. Relative Urban Pressure (Urban Stress V2)
              </h3>
            </div>
            <p className="text-slate-200 font-medium">
              {METHODOLOGY_NOTE}
            </p>
            <p className="text-slate-400">
              Indicators are transformed into empirical percentiles (0 to 100) across all 24 wards. The composite stress score represents relative pressure compared to the rest of Mumbai, rather than an absolute governmental danger threshold.
            </p>
          </div>

          {/* 2. Seven Urban Domains */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-white font-mono uppercase flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              2. Seven Analytical Domains & 15 Audited Indicators
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 font-mono text-[11px]">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
                <span className="font-bold text-rose-400 uppercase">Healthcare</span>
                <p className="text-slate-400 font-sans">Population per healthcare facility; UPHC, dispensary & hospital ratios.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
                <span className="font-bold text-blue-400 uppercase">Education</span>
                <p className="text-slate-400 font-sans">UDISE school coverage, student-teacher ratio, and classroom repair requirements.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
                <span className="font-bold text-cyan-400 uppercase">Sanitation</span>
                <p className="text-slate-400 font-sans">Public toilet seats per 10,000 population and spatial toilet facility density.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
                <span className="font-bold text-purple-400 uppercase">Safety</span>
                <p className="text-slate-400 font-sans">Police station coverage and municipal fire emergency station response catchment.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
                <span className="font-bold text-amber-400 uppercase">Mobility & Transport</span>
                <p className="text-slate-400 font-sans">Suburban railway, metro, monorail, and BEST bus stop node connectivity.</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-white/5 space-y-1">
                <span className="font-bold text-yellow-400 uppercase">Civic Grievances</span>
                <p className="text-slate-400 font-sans">2024 CCRS municipal complaints volume, closure percentage, and average resolution turnaround days.</p>
              </div>
            </div>
          </div>

          {/* 3. Deep Learning & Anomaly Modeling */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-purple-500/30 space-y-2.5">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white font-mono uppercase">
                3. Deep Learning Pipeline: Autoencoder & Spatial Typology
              </h3>
            </div>
            <p className="text-slate-300">
              The AI layer trains a deep Autoencoder network to reconstruct multi-domain municipal feature vectors.
            </p>
            <ul className="space-y-1.5 list-disc list-inside text-slate-400 font-sans">
              <li>
                <strong className="text-purple-300 font-mono">Anomaly Signals (ME, D, C):</strong> Wards whose reconstruction Mean Squared Error (MSE) exceeds the 85th percentile threshold are flagged as structural outlier candidates. This signal highlights unusual combinations of infrastructure assets and is not an empirical diagnosis of failure.
              </li>
              <li>
                <strong className="text-purple-300 font-mono">AI Spatial Clusters (4 Clusters):</strong> Latent space bottleneck features are grouped via deep clustering to identify structural city archetypes without subjective socioeconomic labeling.
              </li>
            </ul>
          </div>

          {/* 4. What-If Scenario Simulation Assumptions */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-emerald-500/30 space-y-2">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white font-mono uppercase">
                4. What-If Scenario Simulation Engine
              </h3>
            </div>
            <p className="text-slate-200">
              {SCENARIO_DISCLAIMER}
            </p>
            <p className="text-slate-400">
              Simulations apply a 20% improvement to selected domain indicators (e.g. +20% healthcare facilities, +20% public toilets, -20% complaint resolution turnaround) and recalculate the percentile ranks against Mumbai's fixed baseline distribution.
            </p>
          </div>

          {/* 5. Environmental Freshness & Quality Control */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-pink-500/30 space-y-2">
            <div className="flex items-center gap-2">
              <Wind className="w-4 h-4 text-pink-400" />
              <h3 className="text-sm font-bold text-white font-mono uppercase">
                5. Environmental Freshness Protocol
              </h3>
            </div>
            <p className="text-slate-400">
              Ambient air quality measurements (PM2.5, PM10, NO2, SO2, O3, CO) from CPCB/MPCB stations are freshness-aware. Wards without active continuous ambient air quality monitoring stations display <span className="font-mono text-pink-300 bg-pink-950/60 px-1 py-0.5 rounded border border-pink-500/20">No recent observation available</span> to prevent zero-value distortion.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950 border-t border-white/10 flex items-center justify-between">
          <span className="text-[11px] font-mono text-slate-500">
            Brihanmumbai Municipal Corporation (BMC) GIS Master Data Source
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-colors"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
};
