import React from 'react';
import { 
  GitCompare, 
  X, 
  Trash2, 
  Building2, 
  Activity, 
  Users, 
  Layers, 
  Plus,
  HeartPulse,
  GraduationCap,
  Droplets,
  Shield,
  Bus,
  MessageSquare,
  Trees
} from 'lucide-react';
import { WARD_NAMES, DOMAINS, STRESS_BANDS } from '../../constants';
import { Badge } from '../common/Badge';
import { formatNumber, formatStressScore, getStressColor } from '../../utils/formatters';

export const WardComparisonDrawer = ({
  isOpen,
  onClose,
  comparedWardCodes = [],
  onRemoveFromComparison,
  onClearComparison,
  allWardsData = [],
  wardBaseMap = {},
  onSelectWard
}) => {
  if (!isOpen) return null;

  const comparedWardsData = comparedWardCodes.map(code => {
    return wardBaseMap[code] || allWardsData.find(w => w.ward_code === code) || { ward_code: code };
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="w-full max-w-5xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-slate-950 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/30">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white uppercase font-mono">
                  Ward Analytical Comparison
                </h2>
                <Badge variant="purple" size="xs">Multi-Ward GIS Inspector</Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Side-by-side indicator analysis across up to 3 Mumbai municipal wards.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {comparedWardCodes.length > 0 && (
              <button
                onClick={onClearComparison}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 text-slate-400 hover:text-rose-400 text-xs font-mono transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear All</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {comparedWardsData.length === 0 ? (
            <div className="text-center py-16 space-y-3">
              <Building2 className="w-12 h-12 text-slate-600 mx-auto" />
              <h3 className="text-sm font-bold text-slate-300 font-mono">No Wards Selected for Comparison</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto font-sans">
                Select up to 3 wards by clicking the compare button on the map or ward detail panel to compare their domain stress indicators side-by-side.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Top Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {comparedWardsData.map(ward => {
                  const code = ward.ward_code;
                  const name = WARD_NAMES[code] || 'Mumbai Ward';
                  const stress = ward.urban_stress !== null && ward.urban_stress !== undefined ? Number(ward.urban_stress) : null;

                  return (
                    <div key={code} className="p-4 rounded-xl bg-slate-950/80 border border-slate-700/80 relative space-y-3">
                      <button
                        onClick={() => onRemoveFromComparison(code)}
                        className="absolute top-3 right-3 text-slate-500 hover:text-rose-400 p-1 rounded hover:bg-slate-800 transition-colors"
                        title="Remove from comparison"
                      >
                        <X className="w-4 h-4" />
                      </button>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-base font-bold font-mono text-cyan-400">Ward {code}</span>
                          <Badge variant="primary" size="xs">{ward.region || 'Mumbai Division'}</Badge>
                        </div>
                        <h4 className="text-xs font-medium text-slate-200 mt-0.5 truncate">{name}</h4>
                      </div>

                      <div className="p-2.5 rounded-lg bg-slate-900/90 border border-white/5 flex items-center justify-between">
                        <div>
                          <span className="text-xs text-slate-300 font-mono block">Relative Urban Pressure</span>
                          <span className="text-[10px] text-slate-500 font-mono">{ward.stress_band || 'Moderate'}</span>
                        </div>
                        <span className="text-sm font-bold font-mono" style={{ color: getStressColor(ward.stress_band, stress) }}>
                          {formatStressScore(stress)} {stress !== null ? 'pts' : ''}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                        <div className="p-1.5 rounded bg-slate-900/60 border border-white/5">
                          <span className="text-[10px] text-slate-500 uppercase block">Population</span>
                          <span className="font-bold text-white">{formatNumber(ward.population_2011)}</span>
                        </div>
                        <div className="p-1.5 rounded bg-slate-900/60 border border-white/5">
                          <span className="text-[10px] text-slate-500 uppercase block">Density (km²)</span>
                          <span className="font-bold text-white">
                            {ward.population_density_per_sq_km ? Number(ward.population_density_per_sq_km).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : 'No data'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* 7-Domain Stress Comparison Grid */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-white/10 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-white/10">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-cyan-400" />
                    7-Domain Stress Comparison Matrix
                  </span>
                  <Badge variant="derived" size="xs">Percentile Scores</Badge>
                </div>

                <div className="space-y-3 pt-1">
                  {DOMAINS.map(dom => (
                    <div key={dom.key} className="space-y-1.5 p-2 rounded-lg bg-slate-900/40 border border-white/5">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-bold text-slate-200">{dom.name}</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {comparedWardsData.map(ward => {
                          const val = ward[dom.key] !== null && ward[dom.key] !== undefined && !isNaN(ward[dom.key]) ? Number(ward[dom.key]) : null;
                          const color = val !== null ? getStressColor(val) : '#64748b';
                          return (
                            <div key={ward.ward_code} className="space-y-1">
                              <div className="flex items-center justify-between text-[11px] font-mono">
                                <span className="text-slate-400">Ward {ward.ward_code}:</span>
                                <span className="font-bold" style={{ color }}>{val !== null ? `${val.toFixed(1)}%` : 'No data'}</span>
                              </div>
                              <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden">
                                {val !== null ? (
                                  <div 
                                    className="h-full rounded-full transition-all duration-300"
                                    style={{ width: `${Math.min(100, Math.max(0, val))}%`, backgroundColor: color }}
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
                  ))}
                </div>
              </div>

              {/* Infrastructure Assets Comparison Matrix */}
              <div className="p-4 rounded-xl bg-slate-950/80 border border-white/10 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-white/10">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
                    <Building2 className="w-4 h-4 text-cyan-400" />
                    Observed Facility Counts
                  </span>
                  <Badge variant="observed" size="xs">GIS Records</Badge>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
                      <tr>
                        <th className="p-2.5">Indicator</th>
                        {comparedWardsData.map(w => (
                          <th key={w.ward_code} className="p-2.5 text-right font-bold text-cyan-400">
                            Ward {w.ward_code}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      <tr>
                        <td className="p-2.5 text-slate-300">Schools Total</td>
                        {comparedWardsData.map(w => (
                          <td key={w.ward_code} className="p-2.5 text-right font-bold text-white">
                            {formatNumber(w.school_count ?? w.udise_city_schools)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300">Healthcare Facilities</td>
                        {comparedWardsData.map(w => (
                          <td key={w.ward_code} className="p-2.5 text-right font-bold text-white">
                            {formatNumber(w.healthcare_facilities)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300">Public Toilets Total</td>
                        {comparedWardsData.map(w => (
                          <td key={w.ward_code} className="p-2.5 text-right font-bold text-white">
                            {formatNumber(w.functional_toilets_total)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300">Public Transport Nodes</td>
                        {comparedWardsData.map(w => (
                          <td key={w.ward_code} className="p-2.5 text-right font-bold text-white">
                            {formatNumber(w.total_public_transport_nodes ?? w.bus_stop_count)}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="p-2.5 text-slate-300">2024 Civic Complaints</td>
                        {comparedWardsData.map(w => (
                          <td key={w.ward_code} className="p-2.5 text-right font-bold text-white">
                            {formatNumber(w.complaints_received_2024 ?? w.complaints_received)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
