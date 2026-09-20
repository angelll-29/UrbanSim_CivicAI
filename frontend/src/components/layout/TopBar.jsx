import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Building2, 
  Search, 
  Layers, 
  RefreshCw, 
  Info, 
  GitCompare, 
  Sliders, 
  Sparkles,
  ChevronDown,
  ShieldCheck,
  Compass,
  FileText
} from 'lucide-react';
import { WARD_NAMES, LENSES } from '../../constants';
import { Badge } from '../common/Badge';

export const TopBar = ({
  activeLens,
  onSelectLens,
  selectedWardCode,
  onSelectWard,
  onOpenMethodology,
  onOpenComparison,
  comparedWardsCount,
  allWardCodes = [],
  user,
  onLogout
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const filteredWards = allWardCodes.filter(code => {
    const name = WARD_NAMES[code] || '';
    const q = searchQuery.toLowerCase();
    return code.toLowerCase().includes(q) || name.toLowerCase().includes(q);
  });

  const currentLensObj = LENSES.find(l => l.id === activeLens) || LENSES[0];

  const getRoleBadge = (role) => {
    switch (role) {
      case 'CITIZEN':
        return <Badge variant="success" size="xs">Citizen</Badge>;
      case 'URBAN_ANALYST':
        return <Badge variant="primary" size="xs">Urban Analyst</Badge>;
      case 'URBAN_AUTHORITY':
        return <Badge variant="warning" size="xs">Authority</Badge>;
      case 'SYSTEM_ADMIN':
        return <Badge variant="accent" size="xs">Admin</Badge>;
      default:
        return null;
    }
  };

  return (
    <header className="h-14 bg-slate-950/90 backdrop-blur-md border-b border-white/10 px-4 flex items-center justify-between z-30 select-none">
      {/* Brand / Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
          <Building2 className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold tracking-wider text-white uppercase font-mono">
              UrbanSim <span className="text-cyan-400">Civic AI</span>
            </h1>
            <Badge variant="primary" size="xs">Mumbai BMC</Badge>
          </div>
          <p className="text-[11px] text-slate-400 font-mono tracking-wide">
            GIS Urban Intelligence & Scenario Simulation
          </p>
        </div>
      </div>

      {/* Center Search & Workspace Navigation Bar */}
      <div className="flex items-center gap-3">
        {/* Workspace Switcher (Allows instantaneous navigation between authorized views) */}
        {user && (
          <div className="hidden md:flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-lg p-0.5">
            {user.role === 'SYSTEM_ADMIN' && (
              <button
                onClick={() => navigate('/admin')}
                className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                  location.pathname === '/admin' 
                    ? 'bg-purple-950/90 text-purple-300 border border-purple-500/60 shadow-sm' 
                    : 'text-slate-400 hover:text-purple-300 hover:bg-slate-800/60'
                }`}
              >
                Admin Console
              </button>
            )}
            {(user.role === 'SYSTEM_ADMIN' || user.role === 'URBAN_ANALYST' || user.role === 'URBAN_AUTHORITY') && (
              <button
                onClick={() => navigate('/analyst')}
                className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                  location.pathname === '/analyst' 
                    ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-500/60 shadow-sm' 
                    : 'text-slate-400 hover:text-cyan-300 hover:bg-slate-800/60'
                }`}
              >
                Analyst GIS
              </button>
            )}
            {(user.role === 'SYSTEM_ADMIN' || user.role === 'URBAN_AUTHORITY') && (
              <button
                onClick={() => navigate('/authority')}
                className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                  location.pathname === '/authority' 
                    ? 'bg-amber-950/90 text-amber-300 border border-amber-500/60 shadow-sm' 
                    : 'text-slate-400 hover:text-amber-300 hover:bg-slate-800/60'
                }`}
              >
                Authority Ops
              </button>
            )}
            <button
              onClick={() => navigate('/citizen')}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                location.pathname === '/citizen' 
                  ? 'bg-emerald-950/90 text-emerald-300 border border-emerald-500/60 shadow-sm' 
                  : 'text-slate-400 hover:text-emerald-300 hover:bg-slate-800/60'
              }`}
            >
              Citizen View
            </button>
          </div>
        )}

        {/* Ward Search Combobox */}
        {allWardCodes.length > 0 && onSelectWard && (
          <div className="relative">
            <div className="flex items-center bg-slate-900/90 border border-slate-700/80 rounded-lg px-2.5 py-1.5 w-56 lg:w-64 focus-within:border-cyan-500/60 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all">
              <Search className="w-3.5 h-3.5 text-slate-400 mr-2 shrink-0" />
              <input
                type="text"
                placeholder="Search ward (GS, Kurla)..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                onFocus={() => setIsSearchOpen(true)}
                className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full"
              />
              {selectedWardCode && (
                <span className="text-[10px] font-mono bg-cyan-950/80 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.2 rounded shrink-0">
                  {selectedWardCode}
                </span>
              )}
            </div>

            {/* Search Dropdown */}
            {isSearchOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setIsSearchOpen(false)}
                />
                <div className="absolute top-full mt-1.5 left-0 w-80 max-h-64 overflow-y-auto bg-slate-900/95 border border-slate-700 rounded-lg shadow-2xl z-50 p-1 divide-y divide-slate-800">
                  {filteredWards.length === 0 ? (
                    <div className="p-3 text-xs text-slate-400 text-center">No matching wards found</div>
                  ) : (
                    filteredWards.map(code => (
                      <button
                        key={code}
                        onClick={() => {
                          onSelectWard(code);
                          setIsSearchOpen(false);
                          setSearchQuery('');
                        }}
                        className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-800/80 rounded transition-colors ${selectedWardCode === code ? 'bg-cyan-950/40 text-cyan-300' : 'text-slate-200'}`}
                      >
                        <div>
                          <span className="font-mono font-bold text-cyan-400 mr-2">Ward {code}</span>
                          <span className="text-slate-300">{WARD_NAMES[code] || ''}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">Select</span>
                      </button>
                    ))
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Current Analytical Lens Badge */}
        {activeLens && (
          <div className="hidden xl:flex items-center gap-2 px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider font-mono">Lens:</span>
            <span className="text-xs font-semibold text-cyan-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              {currentLensObj.name}
            </span>
          </div>
        )}
      </div>

      {/* Right Controls: Comparison, Methodology, User info, Logout */}
      <div className="flex items-center gap-2">
        {/* Ward Comparison Toggle */}
        {onOpenComparison && (
          <button
            onClick={onOpenComparison}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all ${comparedWardsCount > 0 ? 'bg-purple-950/60 border-purple-500/40 text-purple-300 hover:bg-purple-900/60' : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:bg-slate-800'}`}
          >
            <GitCompare className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden sm:inline">Compare</span>
            {comparedWardsCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-purple-500 text-white text-[10px] font-mono flex items-center justify-center">
                {comparedWardsCount}
              </span>
            )}
          </button>
        )}

        {/* Data & Methodology Modal Button */}
        {onOpenMethodology && (
          <button
            onClick={onOpenMethodology}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-medium transition-all"
          >
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Methodology</span>
          </button>
        )}

        {/* User Profile & Logout */}
        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-xs font-medium text-slate-200">{user.name || user.username}</span>
              <div className="flex items-center gap-1">
                {getRoleBadge(user.role)}
              </div>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                title="Sign out of UrbanSim"
                className="px-2.5 py-1.5 bg-slate-900/80 border border-slate-700/60 hover:bg-red-950/50 hover:border-red-500/40 text-slate-300 hover:text-red-300 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5"
              >
                <span>Logout</span>
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
