import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { 
  ZoomIn, 
  ZoomOut, 
  Crosshair, 
  Maximize2, 
  Layers, 
  Sparkles,
  AlertTriangle,
  Info
} from 'lucide-react';
import { 
  WARD_NAMES, 
  STRESS_BANDS, 
  CLUSTER_COLORS, 
  LENSES,
  FACILITY_LAYERS 
} from '../../constants';
import { getStressColor, formatStressScore } from '../../utils/formatters';

const MUMBAI_CENTER = [19.0760, 72.8777];
const DEFAULT_ZOOM = 11;

export const LeafletMap = ({
  geojsonData,
  activeLens,
  selectedWardCode,
  onSelectWard,
  facilityLayersData = {},
  activeLayers = {},
  scenarioResults = []
}) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const geojsonLayerRef = useRef(null);
  const facilityLayerGroupRefs = useRef({});
  const [hoveredWard, setHoveredWard] = useState(null);
  const [isLegendOpen, setIsLegendOpen] = useState(true);

  const selectedWardProps = React.useMemo(() => {
    if (!geojsonData || !geojsonData.features || !selectedWardCode) return null;
    const feat = geojsonData.features.find(f => f.properties && f.properties.ward_code === selectedWardCode);
    return feat ? feat.properties : null;
  }, [geojsonData, selectedWardCode]);

  // 1. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: MUMBAI_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
      attributionControl: false,
      minZoom: 10,
      maxZoom: 17
    });

    // Public OpenStreetMap Basemap (No API key required)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      className: 'osm-tiles-subdued',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Custom UrbanSim attribution
    L.control.attribution({
      position: 'bottomright',
      prefix: '<span class="text-[10px] text-slate-500 font-mono">UrbanSim Civic AI | Mumbai BMC Wards</span>'
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Helper function to compute fill color based on active lens
  const getFeatureColor = (props) => {
    if (!props) return '#334155';

    switch (activeLens) {
      case 'livability':
        return getStressColor(props.urban_stress, props.stress_band);

      case 'healthcare':
        return getStressColor(props.healthcare_stress);

      case 'education':
        return getStressColor(props.education_stress);

      case 'safety':
        return getStressColor(props.safety_stress);

      case 'mobility':
        return getStressColor(props.transport_stress);

      case 'sanitation':
        return getStressColor(props.sanitation_stress);

      case 'green_space':
        return getStressColor(props.green_space_stress);

      case 'civic':
        return getStressColor(props.civic_stress);

      case 'clusters':
        return CLUSTER_COLORS[props.cluster] || '#64748b';

      case 'anomalies':
        if (props.anomaly_candidate) {
          return '#f43f5e'; // Highlight Anomaly Candidate (ME, D, C)
        }
        return '#1e293b';

      case 'environment':
        return props.environmental_station_presence ? '#06b6d4' : '#1e293b';

      case 'scenarios':
        // Delta visualization (more negative delta = more reduction)
        const delta = props.best_scenario_change !== null && props.best_scenario_change !== undefined ? Number(props.best_scenario_change) : 0;
        if (delta <= -3.0) return '#10b981';
        if (delta <= -2.0) return '#06b6d4';
        if (delta < 0) return '#3b82f6';
        return '#64748b';

      default:
        return getStressColor(props.urban_stress, props.stress_band);
    }
  };

  // 3. Render / Update GeoJSON Ward Polygons
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !geojsonData) return;

    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
    }

    const geojsonLayer = L.geoJSON(geojsonData, {
      style: (feature) => {
        const props = feature.properties || {};
        const isSelected = selectedWardCode === props.ward_code;
        const isAnomaly = props.anomaly_candidate;

        return {
          fillColor: getFeatureColor(props),
          fillOpacity: isSelected ? 0.88 : 0.62,
          weight: isSelected ? 3 : (activeLens === 'anomalies' && isAnomaly ? 2.5 : 1.2),
          color: isSelected ? '#38bdf8' : (activeLens === 'anomalies' && isAnomaly ? '#f43f5e' : 'rgba(255, 255, 255, 0.25)'),
          dashArray: activeLens === 'anomalies' && isAnomaly && !isSelected ? '4, 4' : null,
        };
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties || {};
        const wardCode = props.ward_code;
        const wardName = WARD_NAMES[wardCode] || 'Mumbai Ward';

        // Tooltip
        const lensObj = LENSES.find(l => l.id === activeLens) || LENSES[0];
        let lensValDisplay = '';
        if (activeLens === 'livability') lensValDisplay = `Relative Urban Pressure: ${formatStressScore(props.urban_stress)} (${props.stress_band || 'Moderate'})`;
        else if (activeLens === 'clusters') lensValDisplay = `AI Typology: ${props.cluster || 'Cluster'}`;
        else if (activeLens === 'anomalies') lensValDisplay = props.anomaly_candidate ? 'AI Anomaly Candidate' : 'Standard Profile';
        else if (activeLens === 'scenarios') lensValDisplay = `Best Scenario Delta: ${props.best_scenario_change !== null && props.best_scenario_change !== undefined ? Number(props.best_scenario_change).toFixed(2) : 'No data'}`;
        else {
          const val = props[lensObj.field];
          lensValDisplay = `${lensObj.name} Stress: ${val !== null && val !== undefined ? Number(val).toFixed(1) : 'No data'}%`;
        }

        layer.bindTooltip(`
          <div class="font-sans">
            <div class="flex items-center gap-1.5 justify-between">
              <span class="font-mono font-bold text-cyan-400 text-xs">Ward ${wardCode}</span>
              <span class="text-[10px] text-slate-400 font-mono">${props.stress_band || ''}</span>
            </div>
            <div class="text-[11px] text-slate-200 truncate mt-0.5 max-w-[200px]">${wardName}</div>
            <div class="text-[11px] font-mono text-cyan-300 mt-1 pt-1 border-t border-white/10">${lensValDisplay}</div>
          </div>
        `, {
          className: 'custom-leaflet-tooltip',
          direction: 'auto',
          sticky: true
        });

        // Event Handlers
        layer.on({
          mouseover: (e) => {
            const l = e.target;
            if (props.ward_code !== selectedWardCode) {
              l.setStyle({
                fillOpacity: 0.82,
                weight: 2,
                color: '#ffffff'
              });
            }
            setHoveredWard({ code: wardCode, name: wardName, props });
          },
          mouseout: (e) => {
            const l = e.target;
            if (props.ward_code !== selectedWardCode) {
              geojsonLayer.resetStyle(l);
            }
            setHoveredWard(null);
          },
          click: (e) => {
            L.DomEvent.stopPropagation(e);
            onSelectWard(wardCode);
          }
        });
      }
    }).addTo(map);

    geojsonLayerRef.current = geojsonLayer;
  }, [geojsonData, activeLens, selectedWardCode]);

  // 4. Center on Selected Ward
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !geojsonLayerRef.current || !selectedWardCode) return;

    geojsonLayerRef.current.eachLayer((layer) => {
      if (layer.feature && layer.feature.properties && layer.feature.properties.ward_code === selectedWardCode) {
        map.fitBounds(layer.getBounds(), {
          padding: [80, 80],
          maxZoom: 13,
          animate: true,
          duration: 0.8
        });
      }
    });
  }, [selectedWardCode]);

  // 5. Render Facility Layers (Points / Markers)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    FACILITY_LAYERS.forEach((layerDef) => {
      const layerId = layerDef.id;
      const isEnabled = !!activeLayers[layerId];
      const data = facilityLayersData[layerId];

      // Remove previous layer if exists
      if (facilityLayerGroupRefs.current[layerId]) {
        map.removeLayer(facilityLayerGroupRefs.current[layerId]);
        delete facilityLayerGroupRefs.current[layerId];
      }

      if (isEnabled && data && data.features) {
        const group = L.layerGroup();

        data.features.forEach((feat) => {
          if (!feat.geometry || !feat.geometry.coordinates) return;
          const coords = feat.geometry.coordinates;
          const latLng = [coords[1], coords[0]];
          const p = feat.properties || {};

          let markerIcon = null;
          let popupContent = '';

          if (layerId === 'environment') {
            const stationName = p.station_name || 'Monitoring Station';
            const provider = p.provider || p.owner || 'CPCB / MPCB';
            const ward = p.urban_ward_code || p.gis_ward || 'Mumbai';

            markerIcon = L.divIcon({
              className: 'custom-aq-icon',
              html: `<div style="background-color: #ec4899; width: 10px; height: 10px; border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 0 10px #ec4899;"></div>`,
              iconSize: [12, 12],
              iconAnchor: [6, 6]
            });

            popupContent = `
              <div class="p-2 min-w-[200px]">
                <div class="flex items-center justify-between gap-2 border-b border-white/10 pb-1">
                  <span class="font-bold text-xs text-pink-400 font-mono">AQ Station</span>
                  <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-pink-950/80 text-pink-300 border border-pink-500/30">Ward ${ward}</span>
                </div>
                <div class="text-xs font-semibold text-white mt-1.5">${stationName}</div>
                <div class="text-[11px] text-slate-400 mt-0.5">Provider: ${provider}</div>
                <div class="mt-2 text-[10px] text-slate-400 bg-slate-900/80 p-1.5 rounded border border-white/5 font-mono">
                  Observations: PM2.5, PM10, NO2, SO2, O3, CO
                </div>
              </div>
            `;
          } else if (layerId === 'healthcare') {
            const facType = p.facility_type || 'Healthcare Facility';
            const name = p.name || p.facility_name || 'Municipal Facility';

            markerIcon = L.divIcon({
              className: 'custom-fac-icon',
              html: `<div style="background-color: #ef4444; width: 8px; height: 8px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 0 6px #ef4444;"></div>`,
              iconSize: [10, 10],
              iconAnchor: [5, 5]
            });

            popupContent = `
              <div class="p-2 min-w-[180px]">
                <div class="text-xs font-bold text-rose-400 uppercase font-mono">${facType}</div>
                <div class="text-xs font-medium text-white mt-1">${name}</div>
                <div class="text-[11px] text-slate-400 mt-1">Ward: ${p.ward || p.urban_ward_code || 'Mumbai'}</div>
              </div>
            `;
          } else {
            markerIcon = L.divIcon({
              className: 'custom-fac-icon',
              html: `<div style="background-color: ${layerDef.color}; width: 7px; height: 7px; border-radius: 50%; border: 1px solid #ffffff;"></div>`,
              iconSize: [8, 8],
              iconAnchor: [4, 4]
            });

            popupContent = `
              <div class="p-2 min-w-[160px]">
                <div class="text-xs font-bold font-mono" style="color: ${layerDef.color}">${layerDef.name}</div>
                <div class="text-xs font-medium text-white mt-1">${p.name || p.station_name || p.facility_name || 'Node'}</div>
                <div class="text-[10px] text-slate-400 mt-0.5">Ward: ${p.ward || p.urban_ward_code || 'Mumbai'}</div>
              </div>
            `;
          }

          const marker = L.marker(latLng, { icon: markerIcon });
          marker.bindPopup(popupContent, { className: 'custom-facility-popup' });
          group.addLayer(marker);
        });

        group.addTo(map);
        facilityLayerGroupRefs.current[layerId] = group;
      }
    });
  }, [facilityLayersData, activeLayers]);

  // Map Controls Handlers
  const handleZoomIn = () => mapInstanceRef.current && mapInstanceRef.current.zoomIn();
  const handleZoomOut = () => mapInstanceRef.current && mapInstanceRef.current.zoomOut();
  const handleReset = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView(MUMBAI_CENTER, DEFAULT_ZOOM, { animate: true });
    }
  };

  return (
    <div className="relative w-full h-full select-none overflow-hidden bg-slate-950">
      {/* Map Container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Floating Map Controls (Bottom Left) */}
      <div className="absolute bottom-6 left-6 z-20 flex flex-col gap-1.5">
        <button
          onClick={handleZoomIn}
          className="w-8 h-8 rounded-lg bg-slate-900/90 border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-800 flex items-center justify-center shadow-lg backdrop-blur transition-all"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="w-8 h-8 rounded-lg bg-slate-900/90 border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-800 flex items-center justify-center shadow-lg backdrop-blur transition-all"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleReset}
          className="w-8 h-8 rounded-lg bg-slate-900/90 border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-800 flex items-center justify-center shadow-lg backdrop-blur transition-all"
          title="Recenter Mumbai"
        >
          <Crosshair className="w-4 h-4" />
        </button>
      </div>

      {/* Dynamic Map Legend */}
      <div className="absolute bottom-6 right-6 z-20">
        <div className="glass-panel rounded-xl p-3 shadow-2xl border border-white/10 max-w-xs transition-all">
          <div className="flex items-center justify-between gap-4 mb-2">
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              {activeLens === 'clusters' ? 'AI Spatial Typologies' : activeLens === 'anomalies' ? 'Autoencoder Anomaly Model' : activeLens === 'scenarios' ? 'Modeled Scenario Delta' : 'Relative Urban Pressure'}
            </span>
            <button 
              onClick={() => setIsLegendOpen(!isLegendOpen)}
              className="text-[10px] text-slate-400 hover:text-white font-mono"
            >
              {isLegendOpen ? 'Hide' : 'Show'}
            </button>
          </div>

          {isLegendOpen && (
            <div className="space-y-1.5 pt-1 border-t border-white/10">
              {activeLens === 'clusters' ? (
                <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono">
                  {Object.entries(CLUSTER_COLORS).map(([name, col]) => (
                    <div key={name} className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: col }}></span>
                      <span className="text-slate-300">{name.replace('_', ' ')}</span>
                    </div>
                  ))}
                </div>
              ) : activeLens === 'anomalies' ? (
                <div className="space-y-1 text-[11px] font-mono">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-rose-500 border border-rose-300"></span>
                    <span className="text-rose-300 font-semibold">Anomaly Candidate (ME, D, C)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-slate-800 border border-slate-700"></span>
                    <span className="text-slate-400">Nominal Reconstruction Error</span>
                  </div>
                  <p className="text-[9px] text-slate-500 mt-1 font-sans leading-tight">
                    Model-derived anomaly signal, not a diagnosis or proof of a real-world problem.
                  </p>
                </div>
              ) : activeLens === 'scenarios' ? (
                <div className="space-y-1 text-[11px] font-mono">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-emerald-500"></span>
                    <span className="text-slate-300">High Reduction (&le; -3.0 pts)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-cyan-500"></span>
                    <span className="text-slate-300">Moderate Reduction (-2.0 to -3.0 pts)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm bg-blue-500"></span>
                    <span className="text-slate-300">Low Reduction (&lt; -2.0 pts)</span>
                  </div>
                  <p className="text-[9px] text-slate-500 mt-1 font-sans leading-tight">
                    Modeled relative-pressure change under fixed-reference assumptions; non-causal.
                  </p>
                </div>
              ) : (
                <div className="space-y-1.5 text-[11px] font-mono">
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
                    <span>Low Pressure (0%)</span>
                    <span>High Pressure (100%)</span>
                  </div>
                  <div className="relative">
                    <div className="flex h-2.5 rounded-full overflow-hidden shadow-inner">
                      <div className="flex-1 bg-emerald-500" title="Very Low (0-20%)"></div>
                      <div className="flex-1 bg-cyan-500" title="Low (20-40%)"></div>
                      <div className="flex-1 bg-yellow-500" title="Moderate (40-60%)"></div>
                      <div className="flex-1 bg-orange-500" title="High (60-80%)"></div>
                      <div className="flex-1 bg-rose-500" title="Very High (80-100%)"></div>
                    </div>
                    {/* Active Selected Ward Needle */}
                    {selectedWardProps && selectedWardProps.urban_stress !== undefined && (
                      <div 
                        className="absolute -top-1 -translate-x-1/2 flex flex-col items-center transition-all duration-300 pointer-events-none"
                        style={{ left: `${Math.min(Math.max(Number(selectedWardProps.urban_stress), 3), 97)}%` }}
                      >
                        <div className="w-2.5 h-2.5 rounded-full bg-white ring-2 ring-cyan-400 shadow-lg"></div>
                      </div>
                    )}
                  </div>
                  {selectedWardProps && selectedWardProps.urban_stress !== undefined ? (
                    <div className="flex items-center justify-between text-[10px] text-cyan-300 font-mono bg-cyan-950/80 px-2 py-1 rounded-md border border-cyan-500/40 mt-1 shadow-sm">
                      <span className="font-bold">Ward {selectedWardCode} Position:</span>
                      <span className="font-bold">{Number(selectedWardProps.urban_stress).toFixed(1)} &bull; {selectedWardProps.stress_band || 'Moderate'}</span>
                    </div>
                  ) : (
                    <div className="flex justify-between text-[9px] text-slate-500 pt-0.5">
                      <span>Very Low</span>
                      <span>Moderate</span>
                      <span>Very High</span>
                    </div>
                  )}
                  <p className="text-[9px] text-slate-500 mt-1 font-sans leading-tight">
                    Percentile-based analytical index across 24 BMC wards; not an official government risk rating.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
