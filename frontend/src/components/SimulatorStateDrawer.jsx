import React, { useState, useEffect } from 'react';
import { 
  X, 
  Database, 
  RefreshCw, 
  Users, 
  Server, 
  Box, 
  DollarSign, 
  ShieldCheck, 
  FileText 
} from 'lucide-react';
import { fetchSimulatorState } from '../services/api';

export default function SimulatorStateDrawer({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('customers');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const state = await fetchSimulatorState();
      setData(state);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-[#0f172a] border-l border-slate-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-indigo-400" />
              <div>
                <h3 className="text-sm font-bold text-white">Stateful Enterprise Simulator Database</h3>
                <p className="text-[11px] text-slate-400">Isolated SQLite tables reflecting production mutations and rollbacks</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={loadData}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Refresh State"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button 
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 px-4 bg-slate-900/40 text-xs font-semibold">
            {[
              { id: 'customers', label: 'Customers', icon: Users },
              { id: 'nodes', label: 'Infra Nodes', icon: Server },
              { id: 'inventory', label: 'Inventory', icon: Box },
              { id: 'credits', label: 'Billing Credits', icon: DollarSign },
              { id: 'audit', label: 'Immutable Audit Trail', icon: FileText },
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-3 px-3 border-b-2 flex items-center space-x-1.5 transition-all ${
                    activeTab === tab.id 
                      ? 'border-indigo-500 text-indigo-300 bg-indigo-500/10' 
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Content */}
          <div className="p-4 flex-1 overflow-y-auto text-xs font-mono">
            {/* Customers */}
            {activeTab === 'customers' && (
              <div className="space-y-2">
                {data?.customers?.map(c => (
                  <div key={c.customer_id} className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 flex justify-between items-center">
                    <div>
                      <div className="font-bold text-slate-200">{c.name} <span className="text-indigo-400">({c.customer_id})</span></div>
                      <div className="text-[11px] text-slate-400">Tier: {c.tier} • LTV: ${c.ltv.toLocaleString()}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-[10px] text-slate-400">Credit Balance</div>
                      <div className="text-sm font-bold text-amber-400">${c.credit_balance.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Nodes */}
            {activeTab === 'nodes' && (
              <div className="space-y-2">
                {data?.nodes?.map(n => (
                  <div key={n.node_id} className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 flex justify-between items-center">
                    <div>
                      <div className="font-bold text-slate-200">{n.node_id}</div>
                      <div className="text-[11px] text-slate-400">Cluster: {n.cluster}</div>
                      {n.last_error && <div className="text-[10px] text-rose-400 mt-1">{n.last_error}</div>}
                    </div>
                    <div className="text-right space-y-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${n.status === 'healthy' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                        {n.status.toUpperCase()}
                      </span>
                      <div className="text-[10px] text-slate-400">CPU: {n.cpu_pct}% | RAM: {n.memory_pct}%</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Inventory */}
            {activeTab === 'inventory' && (
              <div className="space-y-2">
                {data?.inventory?.map(i => (
                  <div key={i.sku} className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 flex justify-between items-center">
                    <div>
                      <div className="font-bold text-slate-200">{i.name}</div>
                      <div className="text-[11px] text-indigo-400">{i.sku} • ${i.unit_price} / unit</div>
                    </div>
                    <div className="text-right">
                      <div className="text-slate-400">Available: <span className="text-emerald-400 font-bold">{i.available_quantity}</span></div>
                      <div className="text-[10px] text-slate-500">Stock: {i.stock_quantity} | Reserved: {i.reserved_quantity}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Credits */}
            {activeTab === 'credits' && (
              <div className="space-y-2">
                {data?.credits?.length === 0 ? (
                  <p className="text-slate-500 text-center py-6">No billing credits issued yet.</p>
                ) : (
                  data?.credits?.map(cr => (
                    <div key={cr.credit_id} className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 flex justify-between items-center">
                      <div>
                        <div className="font-bold text-slate-200">{cr.credit_id} • {cr.customer_id}</div>
                        <div className="text-[11px] text-slate-400">{cr.reason}</div>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${cr.status === 'applied' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}>
                          {cr.status.toUpperCase()}
                        </span>
                        <div className="font-bold text-amber-400 mt-1">${cr.amount.toFixed(2)}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Audit Logs */}
            {activeTab === 'audit' && (
              <div className="space-y-2">
                {data?.audit_logs?.map(a => (
                  <div key={a.id} className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/40 text-[11px] space-y-1">
                    <div className="flex justify-between text-slate-400">
                      <span className="font-bold text-indigo-400">{a.agent}</span>
                      <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-slate-300">{a.event_type}</span>
                    </div>
                    <div className="text-slate-300 truncate">
                      {JSON.stringify(a.details)}
                    </div>
                    <div className="text-[9px] text-slate-500 truncate font-mono">
                      SHA256: {a.checksum}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
