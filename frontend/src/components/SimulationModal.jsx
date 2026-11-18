import React, { useState } from 'react';
import { 
  X, 
  Play, 
  Sparkles, 
  ShieldAlert, 
  Server, 
  Package, 
  KeyRound, 
  Send 
} from 'lucide-react';

export default function SimulationModal({ isOpen, onClose, onSimulate, scenarios }) {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [customTitle, setCustomTitle] = useState('');
  const [customEvent, setCustomEvent] = useState('');
  const [customChannel, setCustomChannel] = useState('email');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleRunScenario = async (scenarioId) => {
    setLoading(true);
    try {
      await onSimulate({ scenario_id: scenarioId, title: '', raw_event: '' });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleRunCustom = async () => {
    if (!customEvent.trim()) return;
    setLoading(true);
    try {
      await onSimulate({
        title: customTitle || 'Custom Inbound Event',
        raw_event: customEvent,
        channel: customChannel
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const getScenarioIcon = (id) => {
    if (id.includes('sla-breach')) return <Server className="w-5 h-5 text-rose-400" />;
    if (id.includes('bulk-order')) return <Package className="w-5 h-5 text-amber-400" />;
    if (id.includes('password')) return <KeyRound className="w-5 h-5 text-cyan-400" />;
    if (id.includes('prompt-injection')) return <ShieldAlert className="w-5 h-5 text-rose-400" />;
    return <Sparkles className="w-5 h-5 text-indigo-400" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-[#111827] border border-slate-700/80 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
              <Play className="w-3.5 h-3.5 text-indigo-400 fill-current" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-white">Simulate Business Operations Event</h3>
              <p className="text-[11px] text-slate-400">Trigger multi-department agent triage across simulated enterprise state</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-800 px-5 bg-slate-900/30">
          <button
            onClick={() => setActiveTab('scenarios')}
            className={`py-2.5 px-4 text-xs font-bold border-b-2 transition-all ${
              activeTab === 'scenarios' 
                ? 'border-indigo-500 text-indigo-300' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Benchmark Scenarios (4)
          </button>
          <button
            onClick={() => setActiveTab('custom')}
            className={`py-2.5 px-4 text-xs font-bold border-b-2 transition-all ${
              activeTab === 'custom' 
                ? 'border-indigo-500 text-indigo-300' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Custom Inbound Event
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-3">
          {activeTab === 'scenarios' ? (
            <div className="grid grid-cols-1 gap-3">
              {scenarios.map(sc => (
                <div 
                  key={sc.id}
                  onClick={() => !loading && handleRunScenario(sc.id)}
                  className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-indigo-950/20 hover:border-indigo-500/50 cursor-pointer transition-all flex items-start space-x-3 group"
                >
                  <div className="w-9 h-9 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                    {getScenarioIcon(sc.id)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5">
                      <h4 className="font-bold text-xs text-white group-hover:text-indigo-200 transition-colors">
                        {sc.title}
                      </h4>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">
                        {sc.channel}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                      {sc.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Incident Title</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="e.g., Billing discrepancy for CUST-10482"
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Inbound Channel</label>
                <select
                  value={customChannel}
                  onChange={(e) => setCustomChannel(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="email">Email</option>
                  <option value="slack">Slack Alert</option>
                  <option value="webhook">B2B Webhook</option>
                  <option value="ticket">Support Ticket</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Raw Unstructured Text</label>
                <textarea
                  rows={6}
                  value={customEvent}
                  onChange={(e) => setCustomEvent(e.target.value)}
                  placeholder="Paste incoming email body, error message, or JSON payload containing customer IDs, amounts, node names..."
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end pt-2">
                <button
                  disabled={loading || !customEvent.trim()}
                  onClick={handleRunCustom}
                  className="px-4 py-2 rounded-lg text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-950 transition-all flex items-center space-x-1.5 disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Dispatch Custom Event</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
