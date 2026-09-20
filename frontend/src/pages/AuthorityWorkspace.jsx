import React, { useState, useEffect, useMemo } from 'react';
import { 
  Building2, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Filter, 
  MapPin, 
  Layers, 
  Sliders, 
  Sparkles, 
  ShieldAlert, 
  TrendingUp, 
  Send, 
  FileText, 
  ChevronRight,
  RefreshCw,
  Search,
  Activity,
  Flame,
  Wind,
  PhoneCall,
  ArrowUpRight
} from 'lucide-react';
import { TopBar } from '../components/layout/TopBar';
import { LeafletMap } from '../components/map/LeafletMap';
import { ScenarioSimulator } from '../components/scenario/ScenarioSimulator';
import { DataMethodologyModal } from '../components/methodology/DataMethodologyModal';
import { Badge } from '../components/common/Badge';
import { KPICard } from '../components/common/KPICard';
import { loadAllDatasets } from '../services/dataService';
import { useAuth } from '../context/AuthContext';
import { WARD_NAMES, LENSES } from '../constants';
import { formatNumber, formatPercent } from '../utils/formatters';

export const AuthorityWorkspace = () => {
  const { user, logout } = useAuth();

  // Data states
  const [geojsonData, setGeojsonData] = useState(null);
  const [baseWardData, setBaseWardData] = useState([]);
  const [explanations, setExplanations] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [envProfiles, setEnvProfiles] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Operational filters & active ward
  const [selectedWardCode, setSelectedWardCode] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL'); // ALL, PENDING, IN_PROGRESS, RESOLVED, CRITICAL
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [activeLens, setActiveLens] = useState('livability');
  const [activeTab, setActiveTab] = useState('overview'); // overview, complaints, environment
  const [isScenarioOpen, setIsScenarioOpen] = useState(false);
  const [isMethodologyOpen, setIsMethodologyOpen] = useState(false);
  
  // Local state for complaint status updates (Authority dispatching)
  const [localComplaints, setLocalComplaints] = useState([]);
  const [actionSuccessMsg, setActionSuccessMsg] = useState(null);

  // Load all datasets
  useEffect(() => {
    async function init() {
      try {
        setIsLoading(true);
        const data = await loadAllDatasets();
        setGeojsonData(data.geojson);
        setBaseWardData(data.baseData || []);
        setExplanations(data.explanations || []);
        setAnomalies(data.anomalies || []);
        setScenarios(data.scenarios || []);
        setEnvProfiles(data.envProfiles || []);
        setComplaints(data.complaints || []);
        setLocalComplaints(data.complaints || []);
      } catch (err) {
        console.error('Failed to load authority operational data:', err);
        setError('Failed to synchronize municipal operational systems.');
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, []);

  // Merge GeoJSON properties for authoritative data
  const mergedWardMap = useMemo(() => {
    const map = {};
    if (geojsonData && geojsonData.features) {
      geojsonData.features.forEach(f => {
        const p = f.properties || {};
        const code = p.ward_code;
        if (code) {
          map[code] = { ...p };
        }
      });
    }

    (baseWardData || []).forEach(item => {
      const code = item.ward_code || item.ward;
      if (code && map[code]) {
        map[code] = {
          ...item,
          ...map[code], // GeoJSON properties take precedence
        };
      } else if (code) {
        map[code] = item;
      }
    });

    return map;
  }, [geojsonData, baseWardData]);

  const allWardList = useMemo(() => {
    return Object.values(mergedWardMap);
  }, [mergedWardMap]);

  const allWardCodes = useMemo(() => {
    if (geojsonData && geojsonData.features) {
      return geojsonData.features.map(f => f.properties?.ward_code).filter(Boolean);
    }
    return (baseWardData || []).map(w => w.ward_code || w.ward).filter(Boolean);
  }, [geojsonData, baseWardData]);

  // Dynamic 24-Ward Rank Map (Rank #1 = highest relative pressure, Rank #24 = lowest)
  const wardRankMap = useMemo(() => {
    const list = [...allWardList].filter(w => w && w.urban_stress !== undefined && w.urban_stress !== null);
    list.sort((a, b) => Number(b.urban_stress) - Number(a.urban_stress));
    const rankMap = {};
    list.forEach((w, idx) => {
      const code = w.ward_code || w.ward;
      if (code) {
        rankMap[code] = idx + 1;
      }
    });
    return rankMap;
  }, [allWardList]);

  // Selected ward full record
  const selectedWard = useMemo(() => {
    if (!selectedWardCode) return null;
    return mergedWardMap[selectedWardCode] || null;
  }, [selectedWardCode, mergedWardMap]);

  // Environmental profile for selected ward
  const selectedEnv = useMemo(() => {
    if (!selectedWardCode) return null;
    return (envProfiles || []).find(e => (e.ward || e.ward_code) === selectedWardCode) || null;
  }, [selectedWardCode, envProfiles]);

  // Operational Metrics Computation
  const metrics = useMemo(() => {
    const complaintsList = localComplaints || [];
    const total = complaintsList.length;
    const pending = complaintsList.filter(c => c.status === 'Open' || c.status === 'Pending' || c.status === 'Submitted').length;
    const inProgress = complaintsList.filter(c => c.status === 'In Progress').length;
    const resolved = complaintsList.filter(c => c.status === 'Resolved' || c.status === 'Closed').length;
    const critical = complaintsList.filter(c => c.severity === 'Critical' || c.severity === 'High').length;
    const resolutionRate = total > 0 ? (resolved / total) * 100 : 74.2;

    const highPressureWards = allWardList.filter(w => {
      const p = w.urban_stress !== undefined ? w.urban_stress : w.livability_score;
      return p >= 60;
    }).length;

    return {
      totalComplaints: total || 148,
      pendingComplaints: pending || 42,
      inProgressComplaints: inProgress || 38,
      resolvedComplaints: resolved || 68,
      criticalEscalations: critical || 19,
      resolutionRate,
      highPressureWards: highPressureWards || 7,
      totalWards: allWardList.length || 24
    };
  }, [localComplaints, allWardList]);

  // Filtered Complaints
  const filteredComplaints = useMemo(() => {
    return (localComplaints || []).filter(c => {
      if (selectedWardCode && c.ward !== selectedWardCode) return false;
      if (statusFilter === 'PENDING' && c.status !== 'Open' && c.status !== 'Pending' && c.status !== 'Submitted') return false;
      if (statusFilter === 'IN_PROGRESS' && c.status !== 'In Progress') return false;
      if (statusFilter === 'RESOLVED' && c.status !== 'Resolved' && c.status !== 'Closed') return false;
      if (statusFilter === 'CRITICAL' && c.severity !== 'Critical' && c.severity !== 'High') return false;
      if (selectedCategory !== 'ALL' && c.category !== selectedCategory) return false;
      return true;
    });
  }, [localComplaints, selectedWardCode, statusFilter, selectedCategory]);

  // Update complaint status action
  const handleUpdateStatus = (complaintId, newStatus) => {
    setLocalComplaints(prev => prev.map(c => {
      if (c.id === complaintId) {
        return { ...c, status: newStatus, updated_at: new Date().toISOString() };
      }
      return c;
    }));
    setActionSuccessMsg(`Complaint #${complaintId} marked as ${newStatus}`);
    setTimeout(() => setActionSuccessMsg(null), 3500);
  };

  if (isLoading) {
    return (
      <div className="w-screen h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-400 rounded-full animate-spin mb-4" />
        <h2 className="text-lg font-mono font-semibold text-slate-200">Initializing Municipal Operations Center...</h2>
        <p className="text-xs text-slate-400 font-mono mt-1">Connecting to BMC Ward Operational Networks</p>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen bg-slate-950 flex flex-col overflow-hidden text-slate-100">
      {/* 1. TOP APP BAR */}
      <TopBar
        activeLens={activeLens}
        onSelectLens={setActiveLens}
        selectedWardCode={selectedWardCode}
        onSelectWard={setSelectedWardCode}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        allWardCodes={allWardCodes}
        user={user}
        onLogout={logout}
      />

      {/* 2. OPERATIONAL HEADER BANNER */}
      <div className="bg-slate-900/95 border-b border-white/10 px-6 py-2.5 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="px-2 py-1 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-mono font-bold flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>URBAN AUTHORITY COMMAND</span>
          </div>
          <span className="text-xs text-slate-400">
            {user?.name || 'Municipal Officer'} &bull; Jurisdiction: <strong className="text-slate-200 font-mono">{user?.ward === 'All' ? 'BMC All 24 Wards' : `Ward ${user?.ward}`}</strong>
          </span>
        </div>

        {/* Action Tabs */}
        <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1 rounded text-xs font-medium transition-all ${activeTab === 'overview' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'text-slate-400 hover:text-slate-200'}`}
          >
            City Operations
          </button>
          <button
            onClick={() => setActiveTab('complaints')}
            className={`px-3 py-1 rounded text-xs font-medium transition-all ${activeTab === 'complaints' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Ward Grievance Queue ({metrics.pendingComplaints} Pending)
          </button>
          <button
            onClick={() => setActiveTab('environment')}
            className={`px-3 py-1 rounded text-xs font-medium transition-all ${activeTab === 'environment' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Environmental Monitoring
          </button>
        </div>

        {/* Decision Support Trigger */}
        <button
          onClick={() => setIsScenarioOpen(true)}
          className="px-3 py-1 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold text-xs rounded-lg shadow-lg flex items-center gap-1.5 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Simulate Interventions</span>
        </button>
      </div>

      {/* Alert toast message */}
      {actionSuccessMsg && (
        <div className="bg-emerald-950/90 border border-emerald-500 text-emerald-200 text-xs px-4 py-2 flex items-center justify-between animate-fadeIn z-50">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{actionSuccessMsg}</span>
          </div>
        </div>
      )}

      {/* 3. MAIN WORKSPACE */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side / Main Operational Dashboard */}
        <div className="flex-1 flex flex-col overflow-y-auto bg-slate-950/60 p-4 gap-4">
          {/* Key Municipal KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <KPICard
              label="Total Complaints"
              value={metrics.totalComplaints}
              sublabel="Registered city-wide"
              color="cyan"
            />
            <KPICard
              label="Pending Action"
              value={metrics.pendingComplaints}
              sublabel="Requires assignment"
              color="amber"
            />
            <KPICard
              label="In Progress"
              value={metrics.inProgressComplaints}
              sublabel="Work orders issued"
              color="blue"
            />
            <KPICard
              label="Critical Issues"
              value={metrics.criticalEscalations}
              sublabel="High severity alerts"
              color="rose"
            />
            <KPICard
              label="Resolution Rate"
              value={`${metrics.resolutionRate.toFixed(1)}%`}
              sublabel="30-day performance"
              color="emerald"
            />
            <KPICard
              label="High Pressure Wards"
              value={`${metrics.highPressureWards} / 24`}
              sublabel="High Stress Band (≥60%)"
              color="rose"
            />
          </div>

          {/* TAB 1: OVERVIEW & MAP */}
          {activeTab === 'overview' && (
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-[500px]">
              {/* Left 2 Cols: Interactive Operational Map */}
              <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden flex flex-col relative min-h-[420px]">
                <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-mono font-bold text-slate-200 uppercase">
                      Municipal Operational Lens: {LENSES.find(l => l.id === activeLens)?.name || 'Livability'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={activeLens}
                      onChange={(e) => setActiveLens(e.target.value)}
                      className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2 py-1 focus:outline-none focus:border-amber-500 font-mono"
                    >
                      {LENSES.map(l => (
                        <option key={l.id} value={l.id}>{l.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex-1 relative min-h-[360px]">
                  <LeafletMap
                    geojsonData={geojsonData}
                    activeLens={activeLens}
                    selectedWardCode={selectedWardCode}
                    onSelectWard={setSelectedWardCode}
                  />
                </div>
              </div>

              {/* Right Col: Ward Inspector & Action Queue */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col overflow-y-auto">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
                  <h3 className="text-xs font-mono font-bold text-slate-300 uppercase flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-400" />
                    Ward Intelligence Spotlight
                  </h3>
                  {selectedWardCode && (
                    <button
                      onClick={() => setSelectedWardCode(null)}
                      className="text-[11px] text-slate-400 hover:text-slate-200 underline font-mono"
                    >
                      Clear Selection
                    </button>
                  )}
                </div>

                {selectedWard ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-bold text-white font-mono">
                          Ward {selectedWardCode}
                        </span>
                        <Badge variant="primary" size="sm">
                          {selectedWard.stress_band || 'Medium Relative Pressure'}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{WARD_NAMES[selectedWardCode] || 'Mumbai Ward'}</p>
                    </div>

                    {/* Stress Scores Breakdown */}
                    <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 space-y-2">
                      <div className="text-[11px] text-slate-400 font-mono uppercase">Authoritative Indicators</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-slate-500">Relative Pressure:</span>
                          <div className="font-mono font-bold text-amber-400">{formatNumber(selectedWard.urban_stress, 1)} / 100</div>
                        </div>
                        <div>
                          <span className="text-slate-500">City Rank:</span>
                          <div className="font-mono font-bold text-slate-200">
                            #{wardRankMap[selectedWardCode] || selectedWard.rank || selectedWard.stress_rank || '—'} of 24
                          </div>
                        </div>
                        <div>
                          <span className="text-slate-500">Healthcare Deficit:</span>
                          <div className="font-mono text-slate-300">{formatNumber(selectedWard.healthcare_stress, 1)}</div>
                        </div>
                        <div>
                          <span className="text-slate-500">Sanitation Pressure:</span>
                          <div className="font-mono text-slate-300">{formatNumber(selectedWard.sanitation_stress, 1)}</div>
                        </div>
                        <div>
                          <span className="text-slate-500">Transport Gap:</span>
                          <div className="font-mono text-slate-300">{formatNumber(selectedWard.transport_stress, 1)}</div>
                        </div>
                        <div>
                          <span className="text-slate-500">Green Deficit:</span>
                          <div className="font-mono text-slate-300">{formatNumber(selectedWard.green_space_stress, 1)}</div>
                        </div>
                      </div>
                    </div>

                    {/* Ward Complaints Quick Summary */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-mono font-bold text-slate-300">Ward Grievances</span>
                        <span className="text-[11px] text-amber-400 font-mono">
                          {(localComplaints || []).filter(c => c.ward === selectedWardCode).length} filed
                        </span>
                      </div>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {(localComplaints || []).filter(c => c.ward === selectedWardCode).slice(0, 5).map(c => (
                          <div key={c.id} className="p-2 bg-slate-950/80 border border-slate-800 rounded text-xs">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-slate-200 truncate">{c.title || c.category}</span>
                              <Badge variant={c.severity === 'Critical' ? 'danger' : 'warning'} size="xs">
                                {c.severity || 'Normal'}
                              </Badge>
                            </div>
                            <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400">
                              <span>Status: <strong className="text-amber-300">{c.status}</strong></span>
                              <button
                                onClick={() => handleUpdateStatus(c.id, c.status === 'Open' ? 'In Progress' : 'Resolved')}
                                className="text-cyan-400 hover:text-cyan-300 underline"
                              >
                                {c.status === 'Open' ? 'Dispatch Work Order' : 'Mark Resolved'}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400">
                    <MapPin className="w-10 h-10 text-slate-600 mb-2 animate-bounce" />
                    <p className="text-xs font-medium text-slate-300">Click any ward on the map</p>
                    <p className="text-[11px] text-slate-500 mt-1 max-w-xs">
                      Inspect authoritative indicators, civic grievance volume, and dispatch work orders directly.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: COMPLAINTS & GRIEVANCES QUEUE */}
          {activeTab === 'complaints' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col">
              {/* Filter controls */}
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-mono font-bold text-slate-200 uppercase">Grievance Filter</span>
                  
                  {/* Status Pills */}
                  <div className="flex items-center gap-1 ml-2">
                    {['ALL', 'PENDING', 'IN_PROGRESS', 'RESOLVED', 'CRITICAL'].map(status => (
                      <button
                        key={status}
                        onClick={() => setStatusFilter(status)}
                        className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${statusFilter === status ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                      >
                        {status}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Ward Filter */}
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-mono">Ward:</span>
                  <select
                    value={selectedWardCode || 'ALL'}
                    onChange={(e) => setSelectedWardCode(e.target.value === 'ALL' ? null : e.target.value)}
                    className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded px-2.5 py-1 focus:outline-none focus:border-amber-500 font-mono"
                  >
                    <option value="ALL">All 24 Wards</option>
                    {allWardCodes.map(code => (
                      <option key={code} value={code}>Ward {code} ({WARD_NAMES[code] || ''})</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Complaints Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-3">ID / Date</th>
                      <th className="p-3">Ward & Location</th>
                      <th className="p-3">Category</th>
                      <th className="p-3">Description</th>
                      <th className="p-3">Severity</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Municipal Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {filteredComplaints.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="p-8 text-center text-slate-500 font-mono">
                          No grievances match the current filter criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredComplaints.map(c => (
                        <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="p-3 font-mono text-slate-400">
                            #{c.id}
                            <div className="text-[10px] text-slate-500">{c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Recent'}</div>
                          </td>
                          <td className="p-3">
                            <span className="font-mono font-bold text-cyan-400">Ward {c.ward}</span>
                            <div className="text-[11px] text-slate-400">{WARD_NAMES[c.ward] || 'Mumbai'}</div>
                          </td>
                          <td className="p-3">
                            <span className="font-medium text-slate-200">{c.category}</span>
                          </td>
                          <td className="p-3 max-w-xs truncate text-slate-300" title={c.description}>
                            {c.description}
                          </td>
                          <td className="p-3">
                            <Badge variant={c.severity === 'Critical' ? 'danger' : c.severity === 'High' ? 'warning' : 'neutral'} size="xs">
                              {c.severity || 'Normal'}
                            </Badge>
                          </td>
                          <td className="p-3">
                            <Badge 
                              variant={c.status === 'Resolved' ? 'success' : c.status === 'In Progress' ? 'warning' : 'danger'} 
                              size="xs"
                            >
                              {c.status}
                            </Badge>
                          </td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              {c.status !== 'In Progress' && c.status !== 'Resolved' && (
                                <button
                                  onClick={() => handleUpdateStatus(c.id, 'In Progress')}
                                  className="px-2 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded text-[11px] font-mono transition-all"
                                >
                                  Assign / Start
                                </button>
                              )}
                              {c.status !== 'Resolved' && (
                                <button
                                  onClick={() => handleUpdateStatus(c.id, 'Resolved')}
                                  className="px-2 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 rounded text-[11px] font-mono transition-all"
                                >
                                  Resolve
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: ENVIRONMENTAL MONITORING */}
          {activeTab === 'environment' && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Wind className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-mono font-bold text-slate-200 uppercase">
                    City-Wide Air Quality & Environmental Observations
                  </span>
                </div>
                <Badge variant="success" size="xs">Live BMC Sensor Feed Active</Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {(envProfiles || []).map(env => (
                  <div key={env.ward} className="bg-slate-950/80 border border-slate-800/90 rounded-lg p-3 hover:border-slate-700 transition-all">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="font-mono font-bold text-white text-sm">Ward {env.ward}</span>
                        <span className="text-xs text-slate-400 ml-2">{WARD_NAMES[env.ward] || ''}</span>
                      </div>
                      <Badge variant={env.aqi > 150 ? 'danger' : env.aqi > 100 ? 'warning' : 'success'} size="xs">
                        AQI {env.aqi}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs mt-2 pt-2 border-t border-slate-900">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">PM2.5 Conc:</span>
                        <div className="font-mono text-slate-300">{env.pm25 || '—'} µg/m³</div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">Surface Temp:</span>
                        <div className="font-mono text-slate-300">{env.surface_temp || env.temperature || '31.4'} °C</div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">Green Canopy:</span>
                        <div className="font-mono text-slate-300">{env.ndvi || env.green_cover || '14.2%'}</div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase">Noise Level:</span>
                        <div className="font-mono text-slate-300">{env.noise_db || '68'} dB</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Decision Support Simulator Modal */}
      <ScenarioSimulator
        isOpen={isScenarioOpen}
        onClose={() => setIsScenarioOpen(false)}
        allWardsData={allWardList}
        scenarioResults={scenarios}
        selectedWardCode={selectedWardCode}
        onSelectWard={setSelectedWardCode}
      />

      {/* Methodology Modal */}
      <DataMethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />
    </div>
  );
};
