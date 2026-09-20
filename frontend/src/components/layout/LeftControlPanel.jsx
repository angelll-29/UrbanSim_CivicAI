import React from 'react';
import { 
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
  Eye,
  EyeOff,
  RotateCcw,
  Layers,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { LENSES, FACILITY_LAYERS } from '../../constants';
import { Badge } from '../common/Badge';

const iconMap = {
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
  Sliders
};

export const LeftControlPanel = ({
  activeLens,
  onSelectLens,
  activeLayers,
  onToggleLayer,
  onResetView,
  isCollapsed,
  onToggleCollapse
}) => {
  return (
    <aside className={`relative z-20 transition-all duration-300 ease-in-out flex flex-col h-[calc(100vh-3.5rem)] glass-panel border-r border-white/10 ${isCollapsed ? 'w-12' : 'w-72'}`}>
      {/* Collapse / Expand Toggle Button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3.5 top-6 z-30 w-7 h-7 rounded-full bg-slate-900 border border-slate-700 text-slate-300 hover:text-white flex items-center justify-center shadow-lg transition-transform hover:scale-110"
        title={isCollapsed ? "Expand panel" : "Collapse panel"}
      >
        {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>

      {isCollapsed ? (
        /* Collapsed Icon-Only Strip */
        <div className="flex flex-col items-center py-4 gap-2 h-full overflow-y-auto">
          <span className="text-[10px] font-mono text-slate-500 uppercase rotate-90 my-3">Lenses</span>
          {LENSES.map(lens => {
            const Icon = iconMap[lens.icon] || Activity;
            const isSelected = activeLens === lens.id;
            return (
              <button
                key={lens.id}
                onClick={() => onSelectLens(lens.id)}
                className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${isSelected ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
                title={lens.name}
              >
                <Icon className="w-4 h-4" />
              </button>
            );
          })}
        </div>
      ) : (
        /* Full Expanded Control Panel */
        <div className="flex flex-col h-full overflow-hidden">
          {/* Section: Urban Lenses */}
          <div className="p-3 border-b border-white/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                Urban Analytical Lenses
              </span>
              <span className="text-[10px] text-slate-500 font-mono">12 Modes</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2.5 space-y-1.5">
            {LENSES.map(lens => {
              const Icon = iconMap[lens.icon] || Activity;
              const isSelected = activeLens === lens.id;

              return (
                <button
                  key={lens.id}
                  onClick={() => onSelectLens(lens.id)}
                  className={`w-full text-left p-2 rounded-lg border transition-all flex items-start gap-2.5 group ${
                    isSelected 
                      ? 'bg-cyan-950/40 border-cyan-500/50 shadow-sm shadow-cyan-500/20 text-white' 
                      : 'bg-slate-900/40 border-white/5 text-slate-300 hover:bg-slate-800/60 hover:border-slate-700/60'
                  }`}
                >
                  <div className={`p-1.5 rounded-md mt-0.5 shrink-0 transition-colors ${
                    isSelected ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-400 group-hover:text-cyan-300'
                  }`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-semibold truncate ${isSelected ? 'text-cyan-300' : 'text-slate-200'}`}>
                        {lens.name}
                      </span>
                      {isSelected && (
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5 font-sans">
                      {lens.desc}
                    </p>
                  </div>
                </button>
              );
            })}

            {/* Section: Facility Layers */}
            <div className="pt-3 mt-3 border-t border-white/10">
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                  Map Infrastructure Layers
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Facility GIS</span>
              </div>

              <div className="space-y-1">
                {FACILITY_LAYERS.map(layer => {
                  const Icon = iconMap[layer.icon] || Layers;
                  const isVisible = !!activeLayers[layer.id];

                  return (
                    <div
                      key={layer.id}
                      onClick={() => onToggleLayer(layer.id)}
                      className={`flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer select-none transition-all ${
                        isVisible 
                          ? 'bg-slate-800/80 border-slate-600/60 text-white' 
                          : 'bg-slate-900/30 border-white/5 text-slate-400 hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: layer.color }}></span>
                        <Icon className="w-3.5 h-3.5 opacity-80" />
                        <span className="text-xs font-medium text-slate-200">{layer.name}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-mono text-slate-500">{layer.count ? layer.count.toLocaleString() : ''}</span>
                        {isVisible ? (
                          <Eye className="w-3.5 h-3.5 text-cyan-400" />
                        ) : (
                          <EyeOff className="w-3.5 h-3.5 text-slate-600" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="p-3 border-t border-white/10 bg-slate-950/60 flex items-center justify-between">
            <button
              onClick={onResetView}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-mono transition-all w-full justify-center"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span>Reset Map View</span>
            </button>
          </div>
        </div>
      )}
    </aside>
  );
};
