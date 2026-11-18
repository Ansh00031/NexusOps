import React, { useState } from 'react';
import { 
  GitCommit, 
  ChevronDown, 
  ChevronRight, 
  Clock, 
  Cpu, 
  CheckCircle2, 
  Sparkles 
} from 'lucide-react';

export default function ReasoningTimeline({ timeline }) {
  const [expanded, setExpanded] = useState({});

  if (!timeline || timeline.length === 0) return null;

  const toggle = (id) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="p-4 rounded-xl border border-slate-800 bg-[#0d131f]/60 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-bold text-slate-200 tracking-wide uppercase">
            Autonomous Agent Reasoning Trace
          </h4>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">
          {timeline.length} Step Pipeline • Fully Audited
        </span>
      </div>

      <div className="space-y-2 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {timeline.map((step, idx) => {
          const isExp = expanded[step.step_id];
          return (
            <div key={step.step_id || idx} className="relative pl-7 text-xs">
              {/* Timeline circle icon */}
              <div className="absolute left-1.5 top-2 -translate-x-1/2 w-4 h-4 rounded-full bg-slate-900 border border-indigo-500 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              </div>

              {/* Step Card */}
              <div className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/40 hover:bg-slate-900/70 transition-all">
                <div 
                  className="flex items-center justify-between cursor-pointer select-none"
                  onClick={() => toggle(step.step_id)}
                >
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 font-mono text-[10px] font-bold">
                      {step.agent_name}
                    </span>
                    <span className="font-semibold text-slate-200">
                      {step.title}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                    <span className="flex items-center space-x-1 font-mono text-[10px]">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{step.duration_ms}ms</span>
                    </span>
                    <span className="text-indigo-400 font-mono text-[10px]">
                      {(step.confidence * 100).toFixed(0)}% conf
                    </span>
                    {isExp ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
                  </div>
                </div>

                {/* Collapsible Details */}
                {isExp && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/80 font-mono text-[11px] text-slate-300 bg-black/30 p-2 rounded">
                    <pre className="whitespace-pre-wrap overflow-x-auto">
                      {JSON.stringify(step.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
