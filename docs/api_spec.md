# NexusOps REST & WebSocket API Specification

## Base URL
`http://localhost:8080/api`

---

## 1. Incidents API

### `POST /api/incidents`
Ingests a new operational event or benchmark scenario and executes the multi-agent pipeline.

**Request Body:**
```json
{
  "title": "Production Outage on node-eu-prod-04",
  "raw_event": "From: cto@acme.com\nSubject: Outage on node-eu-prod-04...",
  "channel": "email",
  "scenario_id": "scenario-sla-breach-250"
}
```

**Response (200 OK):**
```json
{
  "id": "inc-65fe0010",
  "title": "Enterprise SLA Breach & $250 Refund Demand",
  "status": "triaged",
  "sla_priority": "CRITICAL",
  "financial_impact": 250.0,
  "triage": { ... },
  "context": { ... },
  "actions": [ ... ],
  "reasoning_timeline": [ ... ]
}
```

### `GET /api/incidents`
Lists all operational incidents ordered by SLA Priority (`CRITICAL` > `HIGH` > `MEDIUM` > `LOW`) and financial impact descending.

### `GET /api/incidents/{incident_id}`
Returns full incident telemetry, reasoning steps, and proposed actions.

---

## 2. Actions & HITL Approval API

### `POST /api/actions/{action_id}/approve`
Approve a proposed action. Executes the action against the stateful enterprise simulator.

**Request Body:**
```json
{
  "comment": "Approved per Tier-1 VIP SLA terms."
}
```

### `POST /api/actions/{action_id}/reject`
Rejects a proposed action with manager rationale.

**Request Body:**
```json
{
  "comment": "Outage duration does not meet contract SLA threshold."
}
```

### `POST /api/actions/approve-safe`
One-click batch approval for all safe / low-risk actions for an incident.

**Request Body:**
```json
{
  "incident_id": "inc-65fe0010"
}
```

### `POST /api/actions/{action_id}/rollback`
Reverts an executed action in the stateful simulator database.

---

## 3. Simulator & Chaos Controls API

### `GET /api/simulator/scenarios`
Returns the 4 canonical benchmark scenarios.

### `GET /api/simulator/state`
Returns the complete state of the mock enterprise database (Customers, Nodes, Inventory, Credits, Audit log).

### `POST /api/simulator/chaos`
Toggles Chaos Mode (simulating transient 503 failures on CRM queries).

**Request Body:**
```json
{
  "enabled": true
}
```

---

## 4. ROI Metrics API

### `GET /api/metrics`
Returns live operational ROI counters:
```json
{
  "tickets_resolved": 4,
  "hours_saved": 6.75,
  "dollars_protected": 10500.0,
  "mean_time_to_resolution_sec": 14.2,
  "active_incidents": 1,
  "high_stakes_interventions": 5
}
```

---

## 5. Live WebSocket API

### `ws://localhost:8080/ws/incidents/{incident_id}`
Streams live pipeline events and status transitions.
