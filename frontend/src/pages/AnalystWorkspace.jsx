import React, { useState, useEffect, useMemo } from 'react';
import { TopBar } from '../components/layout/TopBar';
import { LeftControlPanel } from '../components/layout/LeftControlPanel';
import { RightIntelligencePanel } from '../components/layout/RightIntelligencePanel';
import { LeafletMap } from '../components/map/LeafletMap';
import { ScenarioSimulator } from '../components/scenario/ScenarioSimulator';
import { WardComparisonDrawer } from '../components/comparison/WardComparisonDrawer';
import { DataMethodologyModal } from '../components/methodology/DataMethodologyModal';
import { loadAllDatasets, loadFacilityLayerData } from '../services/dataService';
import { FACILITY_LAYERS } from '../constants';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Sparkles } from 'lucide-react';
import { Badge } from '../components/common/Badge';

export const AnalystWorkspace = () => {
  const { user, logout } = useAuth();

  // Application State
  const [geojsonData, setGeojsonData] = useState(null);
  const [baseWardData, setBaseWardData] = useState([]);
  const [explanations, setExplanations] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [anomalyFeatures, setAnomalyFeatures] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [envProfiles, setEnvProfiles] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active Controls & Navigation
  const [activeLens, setActiveLens] = useState('livability');
  const [selectedWardCode, setSelectedWardCode] = useState(null);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);

  // Facility Layers State & Cache
  const [activeLayers, setActiveLayers] = useState({
    environment: true,
    healthcare: false,
    schools: false,
    transport: false,
    safety: false,
    toilets: false,
    green_spaces: false,
  });
  const [facilityLayersData, setFacilityLayersData] = useState({});

  // Modals & Drawers
  const [isMethodologyOpen, setIsMethodologyOpen] = useState(false);
  const [isComparisonOpen, setIsComparisonOpen] = useState(false);
  const [isScenarioOpen, setIsScenarioOpen] = useState(false);
  const [comparedWards, setComparedWards] = useState([]);

  // 1. Initial Master Data Load
  useEffect(() => {
    async function initData() {
      try {
        setIsLoading(true);
        const data = await loadAllDatasets();
        setGeojsonData(data.geojson);
        setBaseWardData(data.baseData);
        setExplanations(data.explanations);
        setAnomalies(data.anomalies);
        setAnomalyFeatures(data.anomalyFeatures);
        setScenarios(data.scenarios);
        setClusters(data.clusters);
        setEnvProfiles(data.envProfiles);
        setComplaints(data.complaints);
      } catch (err) {
        console.error('Failed to load authoritative UrbanSim data:', err);
        setError('Failed to load spatial intelligence dataset.');
      } finally {
        setIsLoading(false);
      }
    }
    initData();
  }, []);

  // 2. Lazy Load Facility Layers when Toggled On
  useEffect(() => {
    Object.entries(activeLayers).forEach(([layerId, isEnabled]) => {
      if (isEnabled && !facilityLayersData[layerId]) {
        const layerDef = FACILITY_LAYERS.find(l => l.id === layerId);
        if (layerDef && layerDef.file) {
          loadFacilityLayerData(layerDef.file).then(data => {
            if (data) {
              setFacilityLayersData(prev => ({ ...prev, [layerId]: data }));
            }
          });
        }
      }
    });
  }, [activeLayers, facilityLayersData]);

  // Master Ward Codes & Features
  const allWardCodes = useMemo(() => {
    if (!geojsonData || !geojsonData.features) return [];
    return geojsonData.features.map(f => f.properties.ward_code).filter(Boolean);
  }, [geojsonData]);

  // Unified Ward Map: Authoritative GeoJSON properties are strictly preserved as primary source
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

    baseWardData.forEach(item => {
      const code = item.ward_code;
      if (code && map[code]) {
        map[code] = {
          ...item,
          ...map[code],
        };
      } else if (code) {
        map[code] = item;
      }
    });

    return map;
  }, [geojsonData, baseWardData]);

  const allWardsData = useMemo(() => {
    return Object.values(mergedWardMap);
  }, [mergedWardMap]);

  const explanationsMap = useMemo(() => {
    const map = {};
    explanations.forEach(item => {
      if (item.ward_code) map[item.ward_code] = item;
    });
    return map;
  }, [explanations]);

  const anomaliesMap = useMemo(() => {
    const map = {};
    anomalies.forEach(item => {
      if (item.ward_code) map[item.ward_code] = item;
    });
    return map;
  }, [anomalies]);

  const envProfilesMap = useMemo(() => {
    const map = {};
    envProfiles.forEach(item => {
      if (item.ward_code) map[item.ward_code] = item;
    });
    return map;
  }, [envProfiles]);

  // Handlers
  const handleSelectWard = (wardCode) => {
    setSelectedWardCode(prev => prev === wardCode ? null : wardCode);
  };

  const handleToggleLayer = (layerId) => {
    setActiveLayers(prev => ({ ...prev, [layerId]: !prev[layerId] }));
  };

  const handleAddToComparison = (wardCode) => {
    setComparedWards(prev => {
      if (prev.includes(wardCode)) {
        return prev.filter(c => c !== wardCode);
      }
      if (prev.length >= 3) {
        return [...prev.slice(1), wardCode];
      }
      return [...prev, wardCode];
    });
  };

  const handleRemoveFromComparison = (wardCode) => {
    setComparedWards(prev => prev.filter(c => c !== wardCode));
  };

  const handleClearComparison = () => {
    setComparedWards([]);
  };

  const handleResetView = () => {
    setSelectedWardCode(null);
    setActiveLens('livability');
  };

  if (isLoading) {
    return (
      <div className="w-screen h-screen bg-slate-950 flex flex-col items-center justify-center select-none">
        <div className="relative flex items-center justify-center mb-4">
          <div className="w-16 h-16 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin"></div>
          <div className="absolute w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          </div>
        </div>
        <h2 className="text-sm font-bold tracking-widest text-white uppercase font-mono">
          UrbanSim <span className="text-cyan-400">Analyst Workspace</span>
        </h2>
        <p className="text-xs text-slate-500 font-mono mt-1">
          Loading Mumbai BMC 24 Ward Intelligence Master Dataset...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-screen h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 max-w-md">
          <h2 className="text-sm font-bold text-rose-400 uppercase font-mono">Initialization Error</h2>
          <p className="text-xs text-slate-300 mt-2">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-1.5 rounded-lg bg-rose-500 text-slate-950 font-bold text-xs font-mono"
          >
            Retry Synchronization
          </button>
        </div>
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
        onSelectWard={handleSelectWard}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        onOpenComparison={() => setIsComparisonOpen(true)}
        comparedWardsCount={comparedWards.length}
        allWardCodes={allWardCodes}
        user={user}
        onLogout={logout}
      />

      {/* 2. MAIN WORKSPACE (LEFT PANEL + MAP + RIGHT INTELLIGENCE PANEL) */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Control Panel (12 Urban Lenses + Facility Layers) */}
        <LeftControlPanel
          activeLens={activeLens}
          onSelectLens={setActiveLens}
          activeLayers={activeLayers}
          onToggleLayer={handleToggleLayer}
          onResetView={handleResetView}
          isCollapsed={isLeftPanelCollapsed}
          onToggleCollapse={() => setIsLeftPanelCollapsed(!isLeftPanelCollapsed)}
        />

        {/* Central Dominant GIS Map */}
        <main className="flex-1 h-full relative overflow-hidden">
          <LeafletMap
            geojsonData={geojsonData}
            activeLens={activeLens}
            selectedWardCode={selectedWardCode}
            onSelectWard={handleSelectWard}
            facilityLayersData={facilityLayersData}
            activeLayers={activeLayers}
            scenarioResults={scenarios}
          />
        </main>

        {/* Right Intelligence & Evidence Panel */}
        <RightIntelligencePanel
          selectedWardCode={selectedWardCode}
          onSelectWard={handleSelectWard}
          onCloseWard={() => setSelectedWardCode(null)}
          allWardsData={allWardsData}
          wardBaseMap={mergedWardMap}
          explanationsMap={explanationsMap}
          anomaliesMap={anomaliesMap}
          envProfilesMap={envProfilesMap}
          comparedWards={comparedWards}
          onAddToComparison={handleAddToComparison}
          onOpenComparison={() => setIsComparisonOpen(true)}
          onOpenScenarioMode={() => setIsScenarioOpen(true)}
        />
      </div>

      {/* 3. MODALS & DRAWERS */}
      <ScenarioSimulator
        isOpen={isScenarioOpen}
        onClose={() => setIsScenarioOpen(false)}
        allWardsData={allWardsData}
        scenarioResults={scenarios}
        selectedWardCode={selectedWardCode}
        onSelectWard={handleSelectWard}
      />

      <WardComparisonDrawer
        isOpen={isComparisonOpen}
        onClose={() => setIsComparisonOpen(false)}
        comparedWardCodes={comparedWards}
        onRemoveFromComparison={handleRemoveFromComparison}
        onClearComparison={handleClearComparison}
        allWardsData={allWardsData}
        wardBaseMap={mergedWardMap}
        onSelectWard={handleSelectWard}
      />

      <DataMethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />
    </div>
  );
};
