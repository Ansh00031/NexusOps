import React from 'react';
import { 
  Users, 
  Activity, 
  Box, 
  FileCheck2, 
  AlertTriangle, 
  RefreshCcw,
  CheckCircle2,
  XCircle
} from 'lucide-react';

export default function ContextInspector({ context }) {
  if (!context) return null;

  const crm = context.crm || {};
  const infra = context.infra || {};
  const inventory = context.inventory || {};
  const policy = context.policy || {};
  const compliance = policy.compliance_evaluation || [];
  const retries = context.retry_count || 0;
  const degraded = context.degraded_services || [];

  return (
    <div className="space-y-3">
      {/* Resilience Banner if retries or degradation occurred */}
      {(retries > 0 || degraded.length > 0) && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <RefreshCcw className="w-4 h-4 text-amber-400 animate-spin" />
            <span>
              Resilience Triggered: {retries} exponential backoff retry attempts.
              {degraded.length > 0 && ` Degraded services: ${degraded.join(', ')} (operating in fallback mode).`}
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-[10px] font-mono font-bold">
            SELF-HEALED
          </span>
        </div>
      )}

      {/* 4 Multi-Department Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Card 1: CRM Telemetry */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-[#0d131f]/70 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold">
              <Users className="w-4 h-4" />
              <span>Mock CRM Telemetry</span>
            </div>
            <span className="text-[10px] text-slate-500 uppercase font-mono">Customer Intelligence</span>
          </div>

          <div className="space-y-1.5 pt-1 text-slate-300">
            {Object.entries(crm).map(([key, val]) => {
              if (typeof val !== 'object' || !val) return null;
              if (val.status === 'unavailable') {
                return (
                  <div key={key} className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300">
                    <span className="font-bold">{key}:</span> {val.fallback_note || 'Service Unavailable'}
                  </div>
                );
              }
              return (
                <div key={key} className="p-2 rounded bg-slate-900/60 border border-slate-800 space-y-1">
                  <div className="flex justify-between font-bold text-white">
                    <span>{val.name || key}</span>
                    <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-mono">
                      {val.tier || 'Standard'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[11px] text-slate-400">
                    <div>LTV: <span className="text-slate-200 font-mono">${(val.ltv || 0).toLocaleString()}</span></div>
                    <div>Credit Balance: <span className="text-slate-200 font-mono">${val.credit_balance || 0}</span></div>
                    <div className="col-span-2">SLA: <span className="text-indigo-300">{val.sla_level || 'Standard'}</span></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Card 2: Infrastructure Health */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-[#0d131f]/70 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-400 font-bold">
              <Activity className="w-4 h-4" />
              <span>Infra Cluster Telemetry</span>
            </div>
            <span className="text-[10px] text-slate-500 uppercase font-mono">Server Metrics</span>
          </div>

          <div className="space-y-1.5 pt-1 text-slate-300">
            {Object.keys(infra).length === 0 ? (
              <p className="text-slate-500 italic">No specific server nodes targeted.</p>
            ) : (
              Object.entries(infra).map(([nodeId, val]) => {
                if (typeof val !== 'object' || !val) return null;
                const isDegraded = val.status === 'degraded';
                return (
                  <div key={nodeId} className="p-2 rounded bg-slate-900/60 border border-slate-800 space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-white">{nodeId}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        isDegraded ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400'
                      }`}>
                        {val.status?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </div>
                    {/* CPU & Memory bars */}
                    <div className="space-y-1 text-[10px]">
                      <div>
                        <div className="flex justify-between text-slate-400 mb-0.5">
                          <span>CPU Pressure</span>
                          <span className="font-mono text-slate-200">{val.cpu_pct ?? 25}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${val.cpu_pct > 80 ? 'bg-rose-500' : 'bg-indigo-500'}`} 
                            style={{ width: `${Math.min(val.cpu_pct || 25, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    {val.last_error && (
                      <p className="text-[10px] text-rose-300 font-mono bg-rose-950/40 p-1 rounded border border-rose-500/20 line-clamp-2">
                        {val.last_error}
                      </p>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Card 3: Inventory Telemetry */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-[#0d131f]/70 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold">
              <Box className="w-4 h-4" />
              <span>Inventory & Fulfillment</span>
            </div>
            <span className="text-[10px] text-slate-500 uppercase font-mono">Supply Chain</span>
          </div>

          <div className="space-y-1.5 pt-1 text-slate-300">
            {Object.keys(inventory).length === 0 ? (
              <p className="text-slate-500 italic">No inventory SKUs requested.</p>
            ) : (
              Object.entries(inventory).map(([sku, item]) => {
                if (typeof item !== 'object' || !item) return null;
                const available = (item.stock_quantity || 0) - (item.reserved_quantity || 0);
                return (
                  <div key={sku} className="p-2 rounded bg-slate-900/60 border border-slate-800 space-y-1">
                    <div className="flex justify-between font-bold text-white">
                      <span>{item.name || sku}</span>
                      <span className="font-mono text-emerald-400">${item.unit_price}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1 text-[11px] text-slate-400 pt-0.5">
                      <div>Stock: <span className="font-mono text-slate-200">{item.stock_quantity}</span></div>
                      <div>Reserved: <span className="font-mono text-amber-400">{item.reserved_quantity}</span></div>
                      <div>Available: <span className={`font-mono font-bold ${available < 10 ? 'text-rose-400' : 'text-emerald-400'}`}>{available}</span></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Card 4: Corporate Policy & Guardrails Check */}
        <div className="p-3.5 rounded-xl border border-slate-800 bg-[#0d131f]/70 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-amber-400 font-bold">
              <FileCheck2 className="w-4 h-4" />
              <span>Policy Rules & Thresholds</span>
            </div>
            <span className="text-[10px] text-slate-500 uppercase font-mono">Hard Guardrails</span>
          </div>

          <div className="space-y-1.5 pt-1">
            {compliance.length === 0 ? (
              <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 flex items-center space-x-1.5 text-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>All actions adhere within auto-approval corporate thresholds.</span>
              </div>
            ) : (
              compliance.map((c, idx) => (
                <div key={idx} className="p-2 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start space-x-2 text-xs">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0 mt-0.5" />
                  <span className="leading-tight">{c}</span>
                </div>
              ))
            )}

            <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800 flex justify-between">
              <span>Max Auto-Approved Refund:</span>
              <span className="font-mono font-bold text-slate-200">$100.00</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
