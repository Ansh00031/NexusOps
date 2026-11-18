import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricsBanner from './components/MetricsBanner';
import IncidentQueue from './components/IncidentQueue';
import IncidentDetail from './components/IncidentDetail';
import ContextInspector from './components/ContextInspector';
import ReasoningTimeline from './components/ReasoningTimeline';
import ActionDeck from './components/ActionDeck';
import SimulationModal from './components/SimulationModal';
import SimulatorStateDrawer from './components/SimulatorStateDrawer';
import { 
  fetchIncidents, 
  fetchIncident, 
  createIncident, 
  approveAction, 
  rejectAction, 
  approveSafeActions, 
  rollbackAction, 
  fetchMetrics, 
  fetchChaosStatus, 
  toggleChaosMode, 
  fetchScenarios 
} from './services/api';
import { Activity, Inbox, ShieldCheck } from 'lucide-react';

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [chaosMode, setChaosMode] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [isSimModalOpen, setIsSimModalOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);

  // Poll metrics and incident list every 3s
  useEffect(() => {
    const timer = setInterval(() => {
      refreshData();
    }, 3000);
    return () => clearInterval(timer);
  }, [selectedId]);

  // Load detailed incident when selected
  useEffect(() => {
    if (selectedId) {
      loadIncidentDetail(selectedId);
    }
  }, [selectedId]);

  // WebSocket for live streaming updates on selected incident
  useEffect(() => {
    if (!selectedId) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/incidents/${selectedId}`;

    let socket;
    try {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'TIMELINE_STEP_ADDED') {
            loadIncidentDetail(selectedId);
            refreshData();
          }
        } catch (e) {}
      };
    } catch (e) {}

    return () => {
      if (socket) socket.close();
    };
  }, [selectedId]);

  const loadInitialData = async () => {
    try {
      const [incs, met, ch, scs] = await Promise.all([
        fetchIncidents(),
        fetchMetrics(),
        fetchChaosStatus(),
        fetchScenarios()
      ]);
      setIncidents(incs);
      setMetrics(met);
      setChaosMode(ch.chaos_mode);
      setScenarios(scs);

      // Auto-select first incident or seed with scenario if empty
      if (incs.length > 0) {
        setSelectedId(incs[0].id);
      } else if (scs.length > 0) {
        // Automatically simulate Scenario 1 on first launch so user sees rich data immediately
        const initial = await createIncident({ scenario_id: scs[0].id, title: '', raw_event: '' });
        setIncidents([initial]);
        setSelectedId(initial.id);
        const updatedMet = await fetchMetrics();
        setMetrics(updatedMet);
      }
    } catch (e) {
      console.error("Initialization error:", e);
    }
  };

  const refreshData = async () => {
    try {
      const [incs, met] = await Promise.all([
        fetchIncidents(),
        fetchMetrics()
      ]);
      setIncidents(incs);
      setMetrics(met);
    } catch (e) {}
  };

  const loadIncidentDetail = async (id) => {
    setLoadingDetail(true);
    try {
      const inc = await fetchIncident(id);
      setSelectedIncident(inc);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSimulate = async (payload) => {
    try {
      const newInc = await createIncident(payload);
      setIncidents(prev => [newInc, ...prev]);
      setSelectedId(newInc.id);
      await refreshData();
    } catch (e) {
      alert(`Simulation error: ${e.message}`);
    }
  };

  const handleApprove = async (actionId, comment) => {
    try {
      await approveAction(actionId, comment);
      await loadIncidentDetail(selectedId);
      await refreshData();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleReject = async (actionId, comment) => {
    try {
      await rejectAction(actionId, comment);
      await loadIncidentDetail(selectedId);
      await refreshData();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleApproveSafe = async (incidentId) => {
    try {
      await approveSafeActions(incidentId);
      await loadIncidentDetail(selectedId);
      await refreshData();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleRollback = async (actionId) => {
    try {
      await rollbackAction(actionId);
      await loadIncidentDetail(selectedId);
      await refreshData();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleToggleChaos = async () => {
    try {
      const updated = await toggleChaosMode(!chaosMode);
      setChaosMode(updated.chaos_mode);
    } catch (e) {
      alert(e.message);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#090d16] text-slate-100 font-sans overflow-hidden">
      {/* 1. Header Navigation */}
      <Navbar
        chaosMode={chaosMode}
        onToggleChaos={handleToggleChaos}
        onOpenSimulator={() => setIsDrawerOpen(true)}
        onOpenSimulateModal={() => setIsSimModalOpen(true)}
      />

      {/* 2. ROI & Operational Metrics Bar */}
      <MetricsBanner metrics={metrics} />

      {/* 3. Main Command Center Workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Incident Queue */}
        <IncidentQueue
          incidents={incidents}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />

        {/* Center/Right Panel: Incident Inspector & HITL Action Deck */}
        <div className="flex-1 overflow-y-auto p-5 bg-[#090d16]/90 space-y-5">
          {selectedIncident ? (
            <>
              {/* Incident Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs text-indigo-400 font-bold">{selectedIncident.id}</span>
                    <span className="text-slate-500">•</span>
                    <h2 className="text-lg font-extrabold text-white tracking-tight">{selectedIncident.title}</h2>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Channel: <span className="font-mono uppercase text-slate-300">{selectedIncident.channel}</span> • Ingested: {new Date(selectedIncident.created_at).toLocaleString()}
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-bold border tracking-wider ${
                    selectedIncident.status === 'resolved' 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                      : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                  }`}>
                    STATUS: {selectedIncident.status.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Step 1: Raw Inbound Event & Extracted Entities */}
              <IncidentDetail incident={selectedIncident} />

              {/* Step 2: Multi-Department Context & Policy Check */}
              <ContextInspector context={selectedIncident.context} />

              {/* Step 3: Agent Reasoning Trace Timeline */}
              <ReasoningTimeline timeline={selectedIncident.reasoning_timeline} />

              {/* Step 4: Proposed Cross-Functional Actions & HITL Controls */}
              <ActionDeck
                incidentId={selectedIncident.id}
                actions={selectedIncident.actions}
                onApprove={handleApprove}
                onReject={handleReject}
                onApproveSafe={handleApproveSafe}
                onRollback={handleRollback}
              />
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-3">
              <Inbox className="w-12 h-12 text-slate-600" />
              <p className="text-sm">Select an incident from the queue or simulate a new event to inspect.</p>
            </div>
          )}
        </div>
      </div>

      {/* Simulation Modal */}
      <SimulationModal
        isOpen={isSimModalOpen}
        onClose={() => setIsSimModalOpen(false)}
        onSimulate={handleSimulate}
        scenarios={scenarios}
      />

      {/* Simulator SQLite Database Drawer */}
      <SimulatorStateDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}
