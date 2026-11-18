import React from 'react';
import { 
  ShieldCheck, 
  Activity, 
  Flame, 
  Database, 
  Play, 
  Cpu, 
  AlertTriangle 
} from 'lucide-react';

export default function Navbar({ 
  chaosMode, 
  onToggleChaos, 
  onOpenSimulator, 
  onOpenSimulateModal,
  activeModel = "Gemini 2.5 Flash"
}) {
  return (
    <header className="h-16 border-b border-slate-800 bg-[#0d131f]/90 backdrop-blur-md px-6 flex items-center justify-between z-20 sticky top-0">
      {/* Brand & System Status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Activity className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-200 bg-clip-text text-transparent">
                NexusOps
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Autonomous HITL Core
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Multi-Department Operations Platform</p>
          </div>
        </div>

        {/* Simulator Dry-Run Tag */}
        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>SIMULATOR MODE • 0 PROD RISK</span>
        </div>
      </div>

      {/* Middle: Active Model badge */}
      <div className="hidden md:flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300">
        <Cpu className="w-3.5 h-3.5 text-indigo-400" />
        <span className="text-slate-400">Agent LLM:</span>
        <span className="font-semibold text-slate-200">{activeModel}</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Chaos Mode Toggle */}
        <button
          onClick={onToggleChaos}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
            chaosMode 
              ? 'bg-rose-500/20 border-rose-500/60 text-rose-300 shadow-lg shadow-rose-950/40 animate-pulse' 
              : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:border-slate-600'
          }`}
          title="Simulate 503 HTTP microservice transient failure to showcase self-healing retries"
        >
          <Flame className={`w-3.5 h-3.5 ${chaosMode ? 'text-rose-400' : 'text-slate-400'}`} />
          <span>Chaos Mode: {chaosMode ? 'ON (503 FAULT)' : 'OFF'}</span>
        </button>

        {/* Database State Inspector */}
        <button
          onClick={onOpenSimulator}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-600 transition-all"
        >
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span>Simulator DB</span>
        </button>

        {/* Simulate Event Button */}
        <button
          onClick={onOpenSimulateModal}
          className="flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/30 transition-all active:scale-95"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Simulate Event</span>
        </button>
      </div>
    </header>
  );
}
