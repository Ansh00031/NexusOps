import React from 'react';
import { CheckCircle2, Clock, DollarSign, ShieldAlert, Zap } from 'lucide-react';

export default function MetricsBanner({ metrics }) {
  const items = [
    {
      label: 'Tickets Resolved',
      value: metrics?.tickets_resolved ?? 0,
      sub: 'Simulated multi-department',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      label: 'Hours Saved',
      value: `${metrics?.hours_saved ?? 0} hrs`,
      sub: 'Agent triage vs cross-functional MTTR',
      icon: Clock,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      label: 'Dollars Protected',
      value: `$${(metrics?.dollars_protected ?? 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
      sub: 'Policy & injection catches',
      icon: DollarSign,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      label: 'Mean Time To Resolution',
      value: `${metrics?.mean_time_to_resolution_sec ?? 14.5}s`,
      sub: 'Autonomous triage to action',
      icon: Zap,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    },
    {
      label: 'High-Stakes Gated',
      value: metrics?.high_stakes_interventions ?? 0,
      sub: 'HITL manager review enforced',
      icon: ShieldAlert,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 bg-[#0d131f]/60 border-b border-slate-800">
      {items.map((it, idx) => {
        const Icon = it.icon;
        return (
          <div key={idx} className="flex items-center space-x-3.5 p-3 rounded-xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition-all">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${it.bg}`}>
              <Icon className={`w-5 h-5 ${it.color}`} />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-400 tracking-wide uppercase">{it.label}</p>
              <h4 className="text-lg font-extrabold text-white tracking-tight">{it.value}</h4>
              <p className="text-[10px] text-slate-500 truncate max-w-[140px]">{it.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
