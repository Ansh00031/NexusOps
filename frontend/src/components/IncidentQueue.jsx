import React, { useState } from 'react';
import { 
  AlertCircle, 
  Search, 
  Mail, 
  Webhook, 
  Ticket, 
  DollarSign, 
  ShieldAlert, 
  CheckCircle,
  Clock
} from 'lucide-react';

export default function IncidentQueue({ incidents, selectedId, onSelect }) {
  const [search, setSearch] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');

  const filtered = incidents.filter(inc => {
    const matchesSearch = inc.title.toLowerCase().includes(search.toLowerCase()) ||
                          inc.id.toLowerCase().includes(search.toLowerCase()) ||
                          (inc.triage?.intent || '').toLowerCase().includes(search.toLowerCase());
    const matchesPriority = priorityFilter === 'ALL' || inc.sla_priority === priorityFilter;
    return matchesSearch && matchesPriority;
  });

  const getPriorityStyle = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
      case 'HIGH':
        return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
      case 'MEDIUM':
        return 'bg-sky-500/10 border-sky-500/30 text-sky-400';
      default:
        return 'bg-slate-500/10 border-slate-500/30 text-slate-400';
    }
  };

  const getChannelIcon = (channel) => {
    switch (channel?.toLowerCase()) {
      case 'webhook': return <Webhook className="w-3 h-3 text-purple-400" />;
      case 'ticket': return <Ticket className="w-3 h-3 text-cyan-400" />;
      default: return <Mail className="w-3 h-3 text-indigo-400" />;
    }
  };

  return (
    <div className="w-80 md:w-96 flex flex-col border-r border-slate-800 bg-[#0d131f]/40 h-full overflow-hidden select-none">
      {/* Header & Search */}
      <div className="p-3.5 border-b border-slate-800 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-sm text-slate-200">Incident Queue</h3>
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[11px] font-mono text-indigo-400 font-semibold">
              {incidents.length}
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-medium">Sorted by SLA & Impact</span>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tickets, IDs, intents..."
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Priority Filter Tabs */}
        <div className="flex space-x-1">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(p => (
            <button
              key={p}
              onClick={() => setPriorityFilter(p)}
              className={`px-2 py-1 rounded text-[10px] font-semibold transition-all ${
                priorityFilter === p 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Incident List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
        {filtered.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No operational incidents found. Trigger a simulation to start.
          </div>
        ) : (
          filtered.map(inc => {
            const isSelected = inc.id === selectedId;
            const isInjection = inc.triage?.prompt_injection_detected;
            const isResolved = inc.status === 'resolved';

            return (
              <div
                key={inc.id}
                onClick={() => onSelect(inc.id)}
                className={`p-3.5 cursor-pointer transition-all hover:bg-slate-800/40 relative ${
                  isSelected ? 'bg-indigo-950/30 border-l-4 border-l-indigo-500' : ''
                }`}
              >
                {/* Top: SLA Priority, Channel, Status */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-1.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border tracking-wider flex items-center space-x-1 ${getPriorityStyle(inc.sla_priority)}`}>
                      {inc.sla_priority === 'CRITICAL' && <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping mr-0.5" />}
                      <span>{inc.sla_priority}</span>
                    </span>

                    <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-slate-800/80 text-[10px] text-slate-400 font-mono">
                      {getChannelIcon(inc.channel)}
                      <span>{inc.channel}</span>
                    </span>
                  </div>

                  <div className="flex items-center space-x-1 text-[10px] text-slate-400">
                    {isResolved ? (
                      <span className="text-emerald-400 flex items-center space-x-0.5 font-medium">
                        <CheckCircle className="w-3 h-3" />
                        <span>Resolved</span>
                      </span>
                    ) : (
                      <span className="text-slate-500 flex items-center space-x-0.5">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Title */}
                <h4 className="text-xs font-bold text-slate-200 line-clamp-1 mb-1">
                  {inc.title}
                </h4>

                {/* Intent Summary */}
                <p className="text-[11px] text-slate-400 line-clamp-2 mb-2 leading-relaxed">
                  {inc.triage?.executive_summary || inc.raw_event}
                </p>

                {/* Footer tags */}
                <div className="flex items-center justify-between text-[10px]">
                  <div className="flex items-center space-x-1">
                    {/* Primary Dept */}
                    {inc.triage?.routing?.primary_department && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono font-medium">
                        {inc.triage.routing.primary_department}
                      </span>
                    )}

                    {/* Injection warning badge */}
                    {isInjection && (
                      <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30 flex items-center space-x-0.5">
                        <ShieldAlert className="w-2.5 h-2.5" />
                        <span>INJECTION STOPPED</span>
                      </span>
                    )}
                  </div>

                  {/* Financial amount */}
                  {inc.financial_impact > 0 && (
                    <span className="font-mono font-bold text-amber-400 flex items-center">
                      <DollarSign className="w-3 h-3 -mr-0.5" />
                      {inc.financial_impact.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
