import React from 'react';

export const KPICard = ({ label, value, sublabel, icon: Icon, color = 'cyan', badge }) => {
  const colorMap = {
    cyan: 'text-cyan-400 border-cyan-500/20 bg-cyan-950/20',
    emerald: 'text-emerald-400 border-emerald-500/20 bg-emerald-950/20',
    amber: 'text-amber-400 border-amber-500/20 bg-amber-950/20',
    rose: 'text-rose-400 border-rose-500/20 bg-rose-950/20',
    purple: 'text-purple-400 border-purple-500/20 bg-purple-950/20',
    blue: 'text-blue-400 border-blue-500/20 bg-blue-950/20',
  };

  return (
    <div className={`p-2.5 rounded-lg border flex flex-col justify-between transition-all hover:border-slate-600/60 ${colorMap[color] || colorMap.cyan}`}>
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-medium tracking-wide uppercase">{label}</span>
        {Icon && <Icon className="w-4 h-4 opacity-75" />}
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-xl font-bold font-mono tracking-tight text-white">{value}</span>
        {badge && <span className="text-[10px] px-1.5 py-0.2 rounded bg-white/10 text-slate-300 font-mono">{badge}</span>}
      </div>
      {sublabel && <span className="text-[11px] text-slate-400 mt-0.5">{sublabel}</span>}
    </div>
  );
};
