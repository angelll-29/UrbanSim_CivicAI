import React from 'react';
import { 
  Building2, 
  MapPin, 
  Users, 
  Maximize2, 
  Activity, 
  HeartPulse, 
  GraduationCap, 
  Shield, 
  Bus, 
  Droplets, 
  Trees, 
  Wind, 
  MessageSquare, 
  Network, 
  AlertTriangle, 
  Sliders,
  GitCompare,
  X,
  Clock,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { WARD_NAMES, DOMAINS } from '../../constants';
import { Badge } from '../common/Badge';
import { WhyThisWard } from './WhyThisWard';
import { formatNumber, formatStressScore, getStressBandStyle, getStressColor } from '../../utils/formatters';

export const WardDetailPanel = ({
  wardData,
  explanationData,
  anomalyData,
  envProfileData,
  onClose,
  onAddToComparison,
  isCompared
}) => {
  if (!wardData) return null;

  const wardCode = wardData.ward_code;
  const wardName = WARD_NAMES[wardCode] || 'Mumbai Municipal Ward';
  const urbanStress = wardData.urban_stress !== null && wardData.urban_stress !== undefined ? Number(wardData.urban_stress) : null;
  const stressBandLabel = wardData.stress_band || 'Moderate';
  const stressBandStyle = getStressBandStyle(stressBandLabel);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 bg-slate-950/80">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold font-mono text-cyan-400">Ward {wardCode}</span>
              <Badge variant="primary" size="xs">{wardData.region || 'Mumbai Division'}</Badge>
              {wardData.anomaly_candidate && (
                <Badge variant="danger" size="xs">AI Anomaly Signal</Badge>
              )}
            </div>
            <h2 className="text-sm font-semibold text-white mt-0.5 leading-snug">
              {wardName}
            </h2>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => onAddToComparison(wardCode)}
              className={`p-1.5 rounded-lg border text-xs font-mono transition-all ${
                isCompared 
                  ? 'bg-purple-950/80 border-purple-500/50 text-purple-300' 
                  : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800'
              }`}
              title={isCompared ? "Remove from comparison" : "Add to comparison"}
            >
              <GitCompare className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              title="Close Ward Panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Summary KPIs */}
        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-white/10">
          <div className="p-2 rounded bg-slate-900/60 border border-white/5">
            <span className="text-[10px] text-slate-400 font-mono uppercase block">Relative Pressure</span>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-base font-bold font-mono text-white">
                {formatStressScore(urbanStress)}
              </span>
              <span className="text-[10px] font-semibold" style={{ color: stressBandStyle.color }}>
                {stressBandLabel}
              </span>
            </div>
          </div>
          <div className="p-2 rounded bg-slate-900/60 border border-white/5">
            <span className="text-[10px] text-slate-400 font-mono uppercase block">Population</span>
            <span className="text-sm font-bold font-mono text-white block mt-0.5">
              {formatNumber(wardData.population_2011)}
            </span>
          </div>
          <div className="p-2 rounded bg-slate-900/60 border border-white/5">
            <span className="text-[10px] text-slate-400 font-mono uppercase block">Area / Density</span>
            <span className="text-xs font-bold font-mono text-white block mt-0.5">
              {wardData.area_sq_km ? `${Number(wardData.area_sq_km).toFixed(1)} km²` : 'No data'}
            </span>
          </div>
        </div>
      </div>

      {/* Body: Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* WHY THIS WARD FEATURE */}
        <WhyThisWard 
          wardData={wardData} 
          explanationData={explanationData} 
          anomalyData={anomalyData} 
        />

        {/* DOMAIN PROFILE (7 Domains) */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-white/10 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              Municipal Domain Stress Profile
            </span>
            <Badge variant="derived" size="xs">Percentile Scores</Badge>
          </div>

          <div className="space-y-2 pt-1">
            {DOMAINS.map(dom => {
              const val = wardData[dom.key];
              const hasScore = val !== null && val !== undefined && !isNaN(val);
              const score = hasScore ? Number(val) : null;
              const color = score !== null ? getStressColor(null, score) : '#64748b';

              return (
                <div key={dom.key} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300">{dom.name}</span>
                    <span className="font-bold" style={{ color }}>
                      {score !== null ? `${score.toFixed(1)}%` : 'No data'}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                    {score !== null ? (
                      <div 
                        className="h-full rounded-full transition-all duration-500" 
                        style={{ width: `${Math.min(100, Math.max(0, score))}%`, backgroundColor: color }}
                      />
                    ) : (
                      <div className="h-full w-0 bg-slate-800" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* INFRASTRUCTURE MATRIX */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-white/10 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-cyan-400" />
              Observed Infrastructure Assets
            </span>
            <Badge variant="observed" size="xs">Authoritative</Badge>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Schools</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.school_count ?? wardData.udise_city_schools)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Healthcare Facs</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.healthcare_facilities)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Public Toilets</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.functional_toilets_total)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Transit Nodes</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.total_public_transport_nodes ?? wardData.bus_stop_count)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Police Stations</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.police_station_count)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Fire Stations</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.fire_station_count)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">Green Spaces</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.green_space_count)}
              </span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-white/5 flex items-center justify-between">
              <span className="text-slate-400">2024 Grievances</span>
              <span className="font-bold text-white">
                {formatNumber(wardData.complaints_received_2024 ?? wardData.complaints_received)}
              </span>
            </div>
          </div>
        </div>

        {/* ENVIRONMENTAL OBSERVATIONS & FRESHNESS */}
        <div className="p-3.5 rounded-xl bg-slate-900/70 border border-white/10 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <Wind className="w-3.5 h-3.5 text-pink-400" />
              Air Quality & Environment Network
            </span>
            <Badge variant={envProfileData && envProfileData.recent_measurement_count > 0 ? 'success' : 'default'} size="xs">
              {envProfileData && envProfileData.recent_measurement_count > 0 ? 'Active Sensors' : 'No Recent Station'}
            </Badge>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-white/5">
              <span className="text-slate-400">Monitoring Station Presence:</span>
              <span className={wardData.environmental_station_presence ? 'text-pink-400 font-bold' : 'text-slate-500'}>
                {wardData.environmental_station_presence ? 'Yes (Validated Station)' : 'No Station in Ward'}
              </span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-white/5">
              <span className="text-slate-400">Freshness Status:</span>
              <span className="text-slate-300 font-medium">
                {envProfileData && envProfileData.recent_measurement_count > 0 ? 'Recent OpenAQ Observations' : 'Historical Baseline Only'}
              </span>
            </div>
            <p className="text-[10px] text-slate-500 font-sans leading-relaxed pt-1">
              Note: Continuous ambient monitoring data is freshness-aware. Missing sensor measurements are preserved as unavailable rather than interpolated as zero.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
