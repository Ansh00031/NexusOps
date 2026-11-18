const API_BASE = '/api';

export async function fetchIncidents() {
  const res = await fetch(`${API_BASE}/incidents`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchIncident(id) {
  const res = await fetch(`${API_BASE}/incidents/${id}`);
  if (!res.ok) throw new Error('Failed to fetch incident');
  return res.json();
}

export async function createIncident(payload) {
  const res = await fetch(`${API_BASE}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to ingest incident');
  return res.json();
}

export async function approveAction(actionId, comment) {
  const res = await fetch(`${API_BASE}/actions/${actionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ comment })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to approve action');
  }
  return res.json();
}

export async function rejectAction(actionId, comment) {
  const res = await fetch(`${API_BASE}/actions/${actionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ comment })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to reject action');
  }
  return res.json();
}

export async function approveSafeActions(incidentId) {
  const res = await fetch(`${API_BASE}/actions/approve-safe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId })
  });
  if (!res.ok) throw new Error('Failed to approve safe actions');
  return res.json();
}

export async function rollbackAction(actionId) {
  const res = await fetch(`${API_BASE}/actions/${actionId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to rollback action');
  }
  return res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchChaosStatus() {
  const res = await fetch(`${API_BASE}/simulator/chaos`);
  if (!res.ok) return { chaos_mode: false };
  return res.json();
}

export async function toggleChaosMode(enabled) {
  const res = await fetch(`${API_BASE}/simulator/chaos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled })
  });
  if (!res.ok) throw new Error('Failed to toggle chaos mode');
  return res.json();
}

export async function fetchSimulatorState() {
  const res = await fetch(`${API_BASE}/simulator/state`);
  if (!res.ok) throw new Error('Failed to fetch simulator state');
  return res.json();
}

export async function fetchScenarios() {
  const res = await fetch(`${API_BASE}/simulator/scenarios`);
  if (!res.ok) throw new Error('Failed to fetch scenarios');
  return res.json();
}
