import React from 'react';

export const Badge = ({ children, variant = 'default', size = 'sm', className = '' }) => {
  const variantStyles = {
    default: 'bg-slate-800/80 text-slate-300 border-slate-700/60',
    primary: 'bg-cyan-950/60 text-cyan-400 border-cyan-500/30',
    success: 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-950/60 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-950/60 text-rose-400 border-rose-500/30',
    purple: 'bg-purple-950/60 text-purple-400 border-purple-500/30',
    observed: 'bg-blue-950/70 text-blue-300 border-blue-500/30',
    derived: 'bg-cyan-950/70 text-cyan-300 border-cyan-500/30',
    model: 'bg-purple-950/70 text-purple-300 border-purple-500/30',
    scenario: 'bg-amber-950/70 text-amber-300 border-amber-500/30',
  };

  const sizeStyles = {
    xs: 'text-[10px] px-1.5 py-0.5 font-medium',
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-sm px-2.5 py-1 font-semibold',
  };

  return (
    <span className={`inline-flex items-center gap-1 rounded border tracking-wide uppercase font-mono ${variantStyles[variant] || variantStyles.default} ${sizeStyles[size] || sizeStyles.sm} ${className}`}>
      {children}
    </span>
  );
};
