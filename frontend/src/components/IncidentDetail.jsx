import React from 'react';
import { 
  ShieldAlert, 
  Terminal, 
  Tag, 
  Server, 
  DollarSign, 
  AlertOctagon, 
  Layers, 
  User, 
  Package 
} from 'lucide-react';

export default function IncidentDetail({ incident }) {
  if (!incident) return null;

  const isInjection = incident.triage?.prompt_injection_detected;
  const entities = incident.triage?.entities || {};

  return (
    <div className="space-y-4">
      {/* Prompt Injection Alert Banner */}
      {isInjection && (
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-rose-950/80 to-red-900/40 border border-rose-500/40 shadow-lg shadow-rose-950/30 flex items-start space-x-3">
          <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5 animate-bounce" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-rose-200 tracking-wide uppercase">
              Security Quarantine: Adversarial Prompt Injection Blocked
            </h4>
            <p className="text-xs text-rose-300 leading-relaxed">
              The incoming customer message attempted an administrative override to bypass financial guardrails and force an unauthorized $10,000 credit. Untrusted input isolation prevented LLM compliance. Financial actions are locked to 0.
            </p>
          </div>
        </div>
      )}

      {/* Raw Incoming Event Box */}
      <div className="rounded-xl border border-slate-800 bg-[#0b0f17] overflow-hidden">
        <div className="px-3.5 py-2 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-xs font-bold text-slate-300 tracking-wide uppercase">
              Raw Inbound Event Stream
            </span>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 border border-amber-500/20 text-amber-400">
            &lt;UNTRUSTED_CONTENT_BOUNDARY&gt;
          </span>
        </div>
        <div className="p-3.5 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-52 overflow-y-auto bg-black/30">
          {incident.raw_event}
        </div>
      </div>

      {/* Extracted Business Entities */}
      <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/30 space-y-2.5">
        <div className="flex items-center space-x-2">
          <Tag className="w-3.5 h-3.5 text-indigo-400" />
          <h4 className="text-xs font-bold text-slate-300 tracking-wide uppercase">
            Deterministic Extracted Business Entities
          </h4>
        </div>

        <div className="flex flex-wrap gap-2 text-xs">
          {/* Customer IDs */}
          {entities.customer_ids?.map(cid => (
            <span key={cid} className="px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono flex items-center space-x-1">
              <User className="w-3 h-3 text-indigo-400" />
              <span>{cid}</span>
            </span>
          ))}

          {/* Order IDs */}
          {entities.order_ids?.map(oid => (
            <span key={oid} className="px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-300 font-mono flex items-center space-x-1">
              <Layers className="w-3 h-3 text-purple-400" />
              <span>{oid}</span>
            </span>
          ))}

          {/* Dollar Amounts */}
          {entities.financial_amounts?.map(amt => (
            <span key={amt} className="px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 font-mono font-bold flex items-center space-x-1">
              <DollarSign className="w-3 h-3 text-amber-400" />
              <span>${amt.toLocaleString()}</span>
            </span>
          ))}

          {/* Server Nodes */}
          {entities.server_nodes?.map(node => (
            <span key={node} className="px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-mono flex items-center space-x-1">
              <Server className="w-3 h-3 text-cyan-400" />
              <span>{node}</span>
            </span>
          ))}

          {/* Error Codes */}
          {entities.error_codes?.map(err => (
            <span key={err} className="px-2.5 py-1 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono flex items-center space-x-1">
              <AlertOctagon className="w-3 h-3 text-rose-400" />
              <span>{err}</span>
            </span>
          ))}

          {/* SKUs */}
          {entities.skus?.map(sku => (
            <span key={sku} className="px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-mono flex items-center space-x-1">
              <Package className="w-3 h-3 text-emerald-400" />
              <span>{sku}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
