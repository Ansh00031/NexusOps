import time
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.schemas import (
    Incident, IncidentCreate, TriageResult, EnrichedContext, ResolutionPlan,
    ReasoningStep, ActionProposed, ActionStatus, SLAPriority, Department
)
from backend.app.models.database import IncidentRecord, ActionRecord
from backend.app.agents.triage_agent import TriageAgent
from backend.app.agents.enrichment_agent import EnrichmentAgent
from backend.app.agents.resolution_agent import ResolutionAgent
from backend.app.services.audit_logger import AuditLogger

logger = logging.getLogger("nexusops.orchestrator")

class ConnectionManager:
    """Manages active WebSocket or SSE subscribers for live reasoning updates."""
    def __init__(self):
        self.active_connections: Dict[str, List[Any]] = {}

    def register(self, incident_id: str, websocket: Any):
        if incident_id not in self.active_connections:
            self.active_connections[incident_id] = []
        self.active_connections[incident_id].append(websocket)

    def unregister(self, incident_id: str, websocket: Any):
        if incident_id in self.active_connections:
            if websocket in self.active_connections[incident_id]:
                self.active_connections[incident_id].remove(websocket)

    async def broadcast(self, incident_id: str, message: Dict[str, Any]):
        if incident_id in self.active_connections:
            for ws in self.active_connections[incident_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.debug(f"Failed to push WS message to client: {e}")

ws_manager = ConnectionManager()

class NexusOrchestrator:
    """
    Stateful Multi-Agent Orchestrator Pipeline
    Coordinates Agent 1 (Triage) -> Agent 2 (Enrichment) -> Agent 3 (Resolution)
    """

    def __init__(self, db: Session, chaos_mode: Optional[bool] = None):
        self.db = db
        self.chaos_mode = chaos_mode
        self.triage_agent = TriageAgent()
        self.enrichment_agent = EnrichmentAgent(db=db, chaos_mode=chaos_mode)
        self.resolution_agent = ResolutionAgent()

    def process_incident(self, incident_create: IncidentCreate) -> Incident:
        incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow()
        timeline: List[ReasoningStep] = []

        # ----------------------------------------------------
        # Step 1: Ingestion & Boundary Sanitization
        # ----------------------------------------------------
        t0 = time.time()
        step1 = ReasoningStep(
            step_id=f"step-{uuid.uuid4().hex[:6]}",
            agent_name="IngestionEngine",
            title="Untrusted Boundary Sanitization & Event Framing",
            status="completed",
            timestamp=datetime.utcnow(),
            duration_ms=int((time.time() - t0) * 1000),
            confidence=1.0,
            details={"channel": incident_create.channel, "bytes": len(incident_create.raw_event)}
        )
        timeline.append(step1)

        AuditLogger.log(
            db=self.db,
            incident_id=incident_id,
            agent="IngestionEngine",
            event_type="INGESTION",
            details={"title": incident_create.title, "channel": incident_create.channel}
        )

        # ----------------------------------------------------
        # Step 2: Agent 1 (Triage & Decomposition)
        # ----------------------------------------------------
        t1 = time.time()
        triage_result = self.triage_agent.run(
            raw_event=incident_create.raw_event,
            channel=incident_create.channel
        )
        step2 = ReasoningStep(
            step_id=f"step-{uuid.uuid4().hex[:6]}",
            agent_name="TriageAgent",
            title="Entity Extraction & Intent Classification",
            status="completed",
            timestamp=datetime.utcnow(),
            duration_ms=int((time.time() - t1) * 1000),
            confidence=triage_result.confidence_score,
            details={
                "intent": triage_result.intent,
                "priority": triage_result.sla_priority.value,
                "extracted_entities": triage_result.entities.model_dump(),
                "prompt_injection": triage_result.prompt_injection_detected
            }
        )
        timeline.append(step2)

        AuditLogger.log(
            db=self.db,
            incident_id=incident_id,
            agent="TriageAgent",
            event_type="TRIAGE",
            details={
                "intent": triage_result.intent,
                "sla_priority": triage_result.sla_priority.value,
                "prompt_injection": triage_result.prompt_injection_detected,
                "departments": [d.value for d in triage_result.routing.departments]
            }
        )

        # ----------------------------------------------------
        # Step 3: Agent 2 (Context & Policy Enrichment)
        # ----------------------------------------------------
        t2 = time.time()
        enriched_context = self.enrichment_agent.run(triage=triage_result)
        step3 = ReasoningStep(
            step_id=f"step-{uuid.uuid4().hex[:6]}",
            agent_name="EnrichmentAgent",
            title="Telemetry & Corporate Policy Synthesis",
            status="completed",
            timestamp=datetime.utcnow(),
            duration_ms=int((time.time() - t2) * 1000),
            confidence=enriched_context.confidence_score,
            details={
                "retries": enriched_context.retry_count,
                "degraded": enriched_context.degraded_services,
                "policy_flags": enriched_context.policy.get("compliance_evaluation", [])
            }
        )
        timeline.append(step3)

        AuditLogger.log(
            db=self.db,
            incident_id=incident_id,
            agent="EnrichmentAgent",
            event_type="ENRICHMENT",
            details={
                "retries": enriched_context.retry_count,
                "degraded": enriched_context.degraded_services,
                "policy_eval": enriched_context.policy.get("compliance_evaluation", [])
            }
        )

        # ----------------------------------------------------
        # Step 4: Agent 3 (Resolution & Action Plan)
        # ----------------------------------------------------
        t3 = time.time()
        resolution_plan = self.resolution_agent.run(triage=triage_result, context=enriched_context)
        step4 = ReasoningStep(
            step_id=f"step-{uuid.uuid4().hex[:6]}",
            agent_name="ResolutionAgent",
            title="Cross-Functional Action Proposal & Guardrail Evaluation",
            status="completed",
            timestamp=datetime.utcnow(),
            duration_ms=int((time.time() - t3) * 1000),
            confidence=0.97,
            details={
                "total_actions": len(resolution_plan.actions),
                "safe_actions": resolution_plan.auto_approvable_count,
                "hitl_gated_actions": resolution_plan.requires_approval_count,
                "overall_risk": resolution_plan.overall_risk.value
            }
        )
        timeline.append(step4)

        for act in resolution_plan.actions:
            AuditLogger.log(
                db=self.db,
                incident_id=incident_id,
                action_id=act.id,
                agent="ResolutionAgent",
                event_type="ACTION_PROPOSED",
                details={
                    "type": act.type,
                    "target": act.target,
                    "financial_impact": act.financial_impact,
                    "requires_approval": act.requires_approval,
                    "guardrail_trigger": act.guardrail_trigger
                }
            )

        # ----------------------------------------------------
        # Database Persistence
        # ----------------------------------------------------
        total_financial = sum(a.financial_impact for a in resolution_plan.actions)
        record = IncidentRecord(
            id=incident_id,
            title=incident_create.title,
            channel=incident_create.channel,
            raw_event=incident_create.raw_event,
            status="triaged",
            sla_priority=triage_result.sla_priority.value,
            financial_impact=total_financial,
            created_at=created_at,
            updated_at=datetime.utcnow(),
            triage_json=triage_result.model_dump_json(),
            context_json=enriched_context.model_dump_json(),
            timeline_json=json.dumps([s.model_dump() for s in timeline], default=str)
        )
        self.db.add(record)

        for act in resolution_plan.actions:
            act_record = ActionRecord(
                id=act.id,
                incident_id=incident_id,
                department=act.department.value,
                type=act.type,
                target=act.target,
                payload_json=json.dumps(act.payload),
                rationale=act.rationale,
                financial_impact=act.financial_impact,
                risk_level=act.risk_level.value,
                reversibility=act.reversibility,
                rollback_action=act.rollback_action,
                status=act.status.value,
                requires_approval=act.requires_approval,
                guardrail_trigger=act.guardrail_trigger
            )
            self.db.add(act_record)

        self.db.commit()

        # Build Incident response
        incident = Incident(
            id=incident_id,
            title=incident_create.title,
            raw_event=incident_create.raw_event,
            channel=incident_create.channel,
            status="triaged",
            created_at=created_at,
            updated_at=datetime.utcnow(),
            triage=triage_result,
            context=enriched_context,
            actions=resolution_plan.actions,
            reasoning_timeline=timeline,
            sla_priority=triage_result.sla_priority,
            financial_impact=total_financial
        )

        return incident
