import React, { useState, useEffect, useMemo } from 'react';
import { 
  Building2, 
  MapPin, 
  MessageSquarePlus, 
  Search, 
  Send, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Layers, 
  LogOut, 
  User, 
  Wind, 
  Trees, 
  HeartPulse, 
  GraduationCap, 
  Droplets, 
  Bus,
  ShieldAlert,
  FileText,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { LeafletMap } from '../components/map/LeafletMap';
import { Badge } from '../components/common/Badge';
import { KPICard } from '../components/common/KPICard';
import { loadAllDatasets, loadFacilityLayerData } from '../services/dataService';
import { WARD_NAMES, STRESS_BANDS, FACILITY_LAYERS } from '../constants';
import { formatNumber, formatStressScore, getStressColor } from '../utils/formatters';

export const CitizenWorkspace = () => {
  const { user, logout } = useAuth();

  // Data States
  const [geojsonData, setGeojsonData] = useState(null);
  const [baseWardData, setBaseWardData] = useState([]);
  const [envProfiles, setEnvProfiles] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Active Map & Selection State
  const [selectedWardCode, setSelectedWardCode] = useState(user?.ward && user.ward !== 'All' ? user.ward : 'GS');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('explore'); // 'explore', 'submit_complaint', 'track_complaints'

  // Facility Layers for Citizens
  const [activeLayers, setActiveLayers] = useState({
    environment: true,
    healthcare: true,
    schools: false,
    transport: false,
    safety: false,
    toilets: false,
    green_spaces: false,
  });
  const [facilityLayersData, setFacilityLayersData] = useState({});

  // Citizen Complaint Submission Form State
  const [complaintCategory, setComplaintCategory] = useState('Sanitation / Garbage');
  const [complaintWard, setComplaintWard] = useState(user?.ward && user.ward !== 'All' ? user.ward : selectedWardCode || 'GS');
  const [complaintLocation, setComplaintLocation] = useState('');
  const [complaintDesc, setComplaintDesc] = useState('');
  const [complaintPriority, setComplaintPriority] = useState('Medium');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // ----------------------------------------------------
  // ISOLATED USER COMPLAINTS PERSISTENCE (Only shows current citizen's filings)
  // ----------------------------------------------------
  const userStorageKey = useMemo(() => {
    return user?.username ? `urbansim_citizen_complaints_${user.username.toLowerCase()}` : 'urbansim_citizen_complaints_guest';
  }, [user]);

  const [submittedComplaints, setSubmittedComplaints] = useState([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(userStorageKey);
      if (stored) {
        setSubmittedComplaints(JSON.parse(stored));
      } else if (user?.username === 'citizen') {
        // Initial sample tickets only for the demo seed account
        const seedSample = [
          {
            id: 'CCRS-2026-8941',
            category: 'Public Toilet Maintenance',
            ward: 'GS',
            location: 'Near Worli Naka Public Convenience',
            description: 'Sanitation facility door broken and water supply interrupted',
            date: '2026-09-18',
            status: 'In Progress',
            priority: 'High'
          }
        ];
        setSubmittedComplaints(seedSample);
        localStorage.setItem(userStorageKey, JSON.stringify(seedSample));
      } else {
        setSubmittedComplaints([]);
      }
    } catch (e) {
      setSubmittedComplaints([]);
    }
  }, [userStorageKey, user]);

  // Keep complaintWard in sync if user changes selectedWardCode
  useEffect(() => {
    if (selectedWardCode) {
      setComplaintWard(selectedWardCode);
    }
  }, [selectedWardCode]);

  // Load datasets on mount
  useEffect(() => {
    async function init() {
      try {
        setIsLoading(true);
        const data = await loadAllDatasets();
        setGeojsonData(data.geojson);
        setBaseWardData(data.baseData || []);
        setEnvProfiles(data.envProfiles || []);
        setComplaints(data.complaints || []);
      } catch (err) {
        console.error('Failed to load citizen data:', err);
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, []);

  // Lazy load active facility layers
  useEffect(() => {
    Object.entries(activeLayers).forEach(([layerId, isEnabled]) => {
      if (isEnabled && !facilityLayersData[layerId]) {
        const layerDef = FACILITY_LAYERS.find(l => l.id === layerId);
        if (layerDef && layerDef.file) {
          loadFacilityLayerData(layerDef.file).then(data => {
            if (data) setFacilityLayersData(prev => ({ ...prev, [layerId]: data }));
          });
        }
      }
    });
  }, [activeLayers, facilityLayersData]);

  // Unified Ward Map
  const mergedWardMap = useMemo(() => {
    const map = {};
    if (geojsonData && geojsonData.features) {
      geojsonData.features.forEach(f => {
        const p = f.properties || {};
        if (p.ward_code) map[p.ward_code] = { ...p };
      });
    }
    (baseWardData || []).forEach(item => {
      const code = item.ward_code || item.ward;
      if (code && map[code]) {
        map[code] = { ...item, ...map[code] };
      } else if (code) {
        map[code] = item;
      }
    });
    return map;
  }, [geojsonData, baseWardData]);

  const allWardCodes = Object.keys(mergedWardMap);
  const selectedWardData = mergedWardMap[selectedWardCode] || {};
  const selectedWardName = WARD_NAMES[selectedWardCode] || 'Mumbai Ward';
  const selectedEnv = (envProfiles || []).find(e => (e.ward_code || e.ward) === selectedWardCode) || {};

  const handleToggleLayer = (layerId) => {
    setActiveLayers(prev => ({ ...prev, [layerId]: !prev[layerId] }));
  };

  const handleComplaintSubmit = (e) => {
    e.preventDefault();
    if (!complaintDesc.trim() || !complaintLocation.trim()) return;

    const newComplaint = {
      id: `CCRS-2026-${Math.floor(1000 + Math.random() * 9000)}`,
      category: complaintCategory,
      ward: complaintWard,
      location: complaintLocation.trim(),
      description: complaintDesc.trim(),
      date: new Date().toISOString().split('T')[0],
      status: 'Submitted / Awaiting Inspection',
      priority: complaintPriority,
      submitted_by: user?.username || 'Citizen'
    };

    const updated = [newComplaint, ...submittedComplaints];
    setSubmittedComplaints(updated);
    try {
      localStorage.setItem(userStorageKey, JSON.stringify(updated));
    } catch (_) {}

    setSubmitSuccess(true);
    setComplaintLocation('');
    setComplaintDesc('');
    setTimeout(() => setSubmitSuccess(false), 6000);
  };

  return (
    <div className="w-screen h-screen bg-[#07090e] flex flex-col overflow-hidden text-slate-100 select-none">
      {/* Top Header */}
      <header className="h-14 px-4 bg-slate-950/90 border-b border-white/10 flex items-center justify-between z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-wider text-white uppercase font-mono">
                UrbanSim <span className="text-emerald-400">Citizen Portal</span>
              </h1>
              <Badge variant="success" size="xs">Public Participatory GIS</Badge>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              Ward Discovery, Facility Access &amp; Civic Grievances
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveTab('explore')}
            className={`px-3 py-1 rounded-lg transition-all ${
              activeTab === 'explore' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white'
            }`}
          >
            Explore Ward &amp; Facilities
          </button>
          <button
            onClick={() => setActiveTab('submit_complaint')}
            className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'submit_complaint' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white'
            }`}
          >
            <MessageSquarePlus className="w-3.5 h-3.5" />
            <span>File Civic Grievance</span>
          </button>
          <button
            onClick={() => setActiveTab('track_complaints')}
            className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'track_complaints' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-300 hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Track My Grievances ({submittedComplaints.length})</span>
          </button>
        </div>

        {/* User Info & Logout */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono">
            <User className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-200 font-bold">{user?.name || user?.username || 'Citizen'}</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 text-[10px]">
              Ward {user?.ward || selectedWardCode}
            </span>
          </div>

          <button
            onClick={logout}
            title="Sign out of Citizen Portal"
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:bg-rose-950/40 hover:border-rose-500/40 text-slate-300 hover:text-rose-300 text-xs font-mono transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Ward Selector & Community Amenity Toggles */}
        <aside className="w-80 bg-slate-950/95 border-r border-white/10 flex flex-col justify-between overflow-y-auto z-20">
          <div className="p-4 space-y-4">
            {/* Ward Selector Dropdown */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                Select Mumbai Ward
              </label>
              <select
                value={selectedWardCode}
                onChange={(e) => setSelectedWardCode(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              >
                {allWardCodes.map(code => (
                  <option key={code} value={code}>
                    Ward {code} &ndash; {WARD_NAMES[code] || ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Selected Ward Profile Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2.5">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white font-mono">Ward {selectedWardCode}</h3>
                  <p className="text-xs text-slate-400 font-sans">{selectedWardName}</p>
                </div>
                <Badge variant="primary" size="xs">
                  {selectedWardData.region_zone || 'Mumbai'}
                </Badge>
              </div>

              {/* Public Relative Pressure Card */}
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                    Relative Pressure
                  </span>
                  <span className="text-xs font-bold text-slate-300 font-mono">Percentile Index</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold font-mono text-white">
                    {formatNumber(selectedWardData.urban_stress, 1)}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 block">
                    {selectedWardData.stress_band || 'Moderate'}
                  </span>
                </div>
              </div>

              {/* Quick Amenity Counts */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-slate-950/60 border border-white/5">
                  <span className="text-[10px] text-slate-400 block">Schools Total</span>
                  <span className="font-bold text-white">{selectedWardData.schools_count || 120}</span>
                </div>
                <div className="p-2 rounded bg-slate-950/60 border border-white/5">
                  <span className="text-[10px] text-slate-400 block">Healthcare Facs</span>
                  <span className="font-bold text-white">{selectedWardData.healthcare_facilities_count || 17}</span>
                </div>
                <div className="p-2 rounded bg-slate-950/60 border border-white/5">
                  <span className="text-[10px] text-slate-400 block">Public Toilets</span>
                  <span className="font-bold text-white">{selectedWardData.public_toilets_total_seats || '1,223'}</span>
                </div>
                <div className="p-2 rounded bg-slate-950/60 border border-white/5">
                  <span className="text-[10px] text-slate-400 block">Green Spaces</span>
                  <span className="font-bold text-white">{selectedWardData.green_spaces_count || 18}</span>
                </div>
              </div>
            </div>

            {/* Facility Layer Visibility Checkboxes */}
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                Public Map Facilities
              </span>
              <div className="space-y-1.5 font-mono text-xs">
                {[
                  { id: 'healthcare', label: 'Healthcare Facilities', color: 'bg-rose-500' },
                  { id: 'schools', label: 'Schools & Education', color: 'bg-blue-500' },
                  { id: 'transport', label: 'Transport Nodes', color: 'bg-amber-500' },
                  { id: 'safety', label: 'Safety (Police & Fire)', color: 'bg-purple-500' },
                  { id: 'toilets', label: 'Public Toilets', color: 'bg-cyan-500' },
                  { id: 'green_spaces', label: 'Green Spaces', color: 'bg-emerald-500' },
                  { id: 'environment', label: 'AQ Stations (Freshness)', color: 'bg-pink-500' },
                ].map(layer => (
                  <button
                    key={layer.id}
                    onClick={() => handleToggleLayer(layer.id)}
                    className={`w-full flex items-center justify-between p-2 rounded-lg border transition-all text-left ${
                      activeLayers[layer.id]
                        ? 'bg-slate-900 border-slate-700 text-white'
                        : 'bg-slate-950/40 border-transparent text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${layer.color}`}></span>
                      <span>{layer.label}</span>
                    </div>
                    <span className="text-[10px] uppercase">{activeLayers[layer.id] ? 'ON' : 'OFF'}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Central Content Area */}
        <main className="flex-1 flex overflow-hidden relative">
          
          {/* TAB 1: EXPLORE MAP */}
          {activeTab === 'explore' && (
            <div className="w-full h-full relative">
              <LeafletMap
                geojsonData={geojsonData}
                activeLens="livability"
                selectedWardCode={selectedWardCode}
                onSelectWard={setSelectedWardCode}
                facilityLayersData={facilityLayersData}
                activeLayers={activeLayers}
              />
            </div>
          )}

          {/* TAB 2: FILE CIVIC GRIEVANCE */}
          {activeTab === 'submit_complaint' && (
            <div className="flex-1 overflow-y-auto p-8 max-w-2xl mx-auto w-full space-y-6 font-sans">
              <div className="space-y-1">
                <h2 className="text-xl font-bold text-white font-mono uppercase flex items-center gap-2">
                  <MessageSquarePlus className="w-6 h-6 text-emerald-400" />
                  File a Civic Grievance
                </h2>
                <p className="text-xs text-slate-400 font-sans">
                  Submit a geo-tagged issue directly to the Brihanmumbai Municipal Corporation (BMC) Centralized Complaint Redressal System.
                </p>
              </div>

              {submitSuccess && (
                <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-3 animate-fadeIn">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div>
                    <span className="font-bold font-mono block">Grievance Registered Successfully!</span>
                    <span>Your complaint has been assigned to BMC Ward Officer for {selectedWardName}. You can view it under "Track My Grievances".</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleComplaintSubmit} className="space-y-4 text-xs font-sans">
                <div className="space-y-1.5">
                  <label className="font-mono text-slate-300 uppercase tracking-wider text-[11px] block">
                    Grievance Category
                  </label>
                  <select
                    value={complaintCategory}
                    onChange={(e) => setComplaintCategory(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  >
                    <option value="Sanitation / Garbage">Sanitation & Garbage Accumulation</option>
                    <option value="Roads / Potholes">Roads, Potholes & Footpaths</option>
                    <option value="Water Supply / Leakage">Water Supply & Pipeline Leakage</option>
                    <option value="Street Lighting">Street Lighting & Electrical</option>
                    <option value="Drainage / Sewage">Drainage & Sewage Overflow</option>
                    <option value="Public Toilet Maintenance">Public Toilet Maintenance</option>
                    <option value="Pest Control / Dengue Prevention">Pest Control & Vector-borne Health</option>
                    <option value="Illegal Encroachment">Illegal Encroachment & Parking</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-mono text-slate-300 uppercase tracking-wider text-[11px] block">
                    Target BMC Ward
                  </label>
                  <select
                    value={complaintWard}
                    onChange={(e) => setComplaintWard(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  >
                    {allWardCodes.map(code => (
                      <option key={code} value={code}>Ward {code} &ndash; {WARD_NAMES[code] || ''}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-mono text-slate-300 uppercase tracking-wider text-[11px] block">
                    Exact Location / Street Address
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Near Antophill Church, Matunga East"
                    value={complaintLocation}
                    onChange={(e) => setComplaintLocation(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="font-mono text-slate-300 uppercase tracking-wider text-[11px] block">
                    Grievance Description
                  </label>
                  <textarea
                    rows={4}
                    required
                    placeholder="Describe the issue, impact on residents, and any landmarks..."
                    value={complaintDesc}
                    onChange={(e) => setComplaintDesc(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="font-mono text-slate-300 uppercase tracking-wider text-[11px] block">
                    Urgency Priority
                  </label>
                  <div className="flex gap-4 font-mono">
                    {['Low', 'Medium', 'High', 'Emergency'].map(p => (
                      <label key={p} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="priority"
                          value={p}
                          checked={complaintPriority === p}
                          onChange={(e) => setComplaintPriority(e.target.value)}
                          className="accent-emerald-500"
                        />
                        <span className="text-slate-300">{p}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold font-mono uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 transition-all"
                  >
                    <Send className="w-4 h-4" />
                    <span>Submit Grievance to BMC CCRS</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 3: TRACK GRIEVANCES (Only shows current citizen's filed tickets) */}
          {activeTab === 'track_complaints' && (
            <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full space-y-6 font-sans">
              <div className="space-y-1">
                <h2 className="text-xl font-bold text-white font-mono uppercase flex items-center gap-2">
                  <Clock className="w-6 h-6 text-emerald-400" />
                  My Submitted Grievances &amp; Resolution Status
                </h2>
                <p className="text-xs text-slate-400 font-sans">
                  Showing complaints submitted by <strong className="text-emerald-400">{user?.name || user?.username || 'You'}</strong>. Real-time updates and turnaround indicators.
                </p>
              </div>

              {submittedComplaints.length === 0 ? (
                <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
                    <MessageSquarePlus className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-bold text-white font-mono uppercase">No Grievances Filed Yet</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    You have not filed any civic complaints yet. When you submit a complaint for Ward {user?.ward || selectedWardCode}, it will appear here with live tracking.
                  </p>
                  <button
                    onClick={() => setActiveTab('submit_complaint')}
                    className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-xs font-mono transition-all"
                  >
                    File Your First Grievance
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {submittedComplaints.map(comp => (
                    <div key={comp.id} className="p-4 rounded-xl bg-slate-900 border border-slate-700 space-y-2">
                      <div className="flex items-center justify-between font-mono">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-emerald-400 text-xs">{comp.id}</span>
                          <Badge variant="primary" size="xs">Ward {comp.ward}</Badge>
                          <Badge variant={comp.priority === 'High' || comp.priority === 'Emergency' ? 'danger' : 'warning'} size="xs">
                            {comp.priority} Priority
                          </Badge>
                        </div>
                        <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                          comp.status === 'Resolved' 
                            ? 'bg-emerald-950 text-emerald-400 border-emerald-500/30' 
                            : 'bg-amber-950 text-amber-400 border-amber-500/30'
                        }`}>
                          {comp.status}
                        </span>
                      </div>

                      <h4 className="text-xs font-semibold text-white font-mono">{comp.category}</h4>
                      <p className="text-[11px] text-slate-300 font-sans">{comp.location}</p>
                      {comp.description && (
                        <p className="text-[11px] text-slate-400 italic bg-slate-950/60 p-2 rounded border border-slate-800">
                          &ldquo;{comp.description}&rdquo;
                        </p>
                      )}
                      <div className="text-[10px] text-slate-500 font-mono pt-1 border-t border-white/5 flex items-center justify-between">
                        <span>Submitted on {comp.date} by {user?.name || user?.username}</span>
                        <span>Average Ward Turnaround: 5.8 Days</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </main>
      </div>
    </div>
  );
};
