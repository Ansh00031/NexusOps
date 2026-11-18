import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.models.database import get_db, IncidentRecord, ActionRecord
from backend.app.models.schemas import Incident, IncidentCreate, ActionProposed, ReasoningStep, TriageResult, EnrichedContext, SLAPriority, Department, ActionStatus, ActionRiskLevel
from backend.app.agents.orchestrator import NexusOrchestrator, ws_manager
from simulator.scenarios import get_scenario_by_id

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

def record_to_incident(rec: IncidentRecord, db: Session) -> Incident:
    action_records = db.query(ActionRecord).filter(ActionRecord.incident_id == rec.id).all()
    actions = []
    for a in action_records:
        actions.append(ActionProposed(
            id=a.id,
            department=Department(a.department),
            type=a.type,
            target=a.target,
            payload=json.loads(a.payload_json or "{}"),
            rationale=a.rationale,
            financial_impact=a.financial_impact,
            risk_level=ActionRiskLevel(a.risk_level),
            reversibility=a.reversibility,
            rollback_action=a.rollback_action,
            status=ActionStatus(a.status),
            requires_approval=a.requires_approval,
            guardrail_trigger=a.guardrail_trigger,
            manager_comment=a.manager_comment,
            executed_at=a.executed_at,
            execution_result=json.loads(a.execution_result_json) if a.execution_result_json else None
        ))

    triage = TriageResult.model_validate_json(rec.triage_json) if rec.triage_json else None
    context = EnrichedContext.model_validate_json(rec.context_json) if rec.context_json else None
    timeline = [ReasoningStep.model_validate(s) for s in json.loads(rec.timeline_json or "[]")]

    return Incident(
        id=rec.id,
        title=rec.title,
        raw_event=rec.raw_event,
        channel=rec.channel,
        status=rec.status,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        triage=triage,
        context=context,
        actions=actions,
        reasoning_timeline=timeline,
        sla_priority=SLAPriority(rec.sla_priority),
        financial_impact=rec.financial_impact
    )

@router.post("", response_model=Incident)
def create_or_simulate_incident(
    payload: IncidentCreate,
    chaos_mode: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Ingest a new business event (or preconfigured scenario), decompose across agents,
    and persist the generated incident.
    """
    # If scenario_id provided, populate from scenarios
    if payload.scenario_id:
        scenario = get_scenario_by_id(payload.scenario_id)
        payload.title = scenario["title"]
        payload.raw_event = scenario["raw_event"]
        payload.channel = scenario["channel"]

    orchestrator = NexusOrchestrator(db=db, chaos_mode=chaos_mode)
    incident = orchestrator.process_incident(payload)
    return incident

@router.get("", response_model=List[Incident])
def list_incidents(
    db: Session = Depends(get_db)
):
    """
    List operational incidents, ordered by SLA Priority (CRITICAL > HIGH > MEDIUM > LOW)
    and financial impact descending.
    """
    records = db.query(IncidentRecord).all()
    incidents = [record_to_incident(r, db) for r in records]

    # Priority sorting weight
    priority_order = {
        SLAPriority.CRITICAL: 4,
        SLAPriority.HIGH: 3,
        SLAPriority.MEDIUM: 2,
        SLAPriority.LOW: 1
    }

    incidents.sort(
        key=lambda inc: (
            priority_order.get(inc.sla_priority, 0),
            inc.financial_impact,
            inc.created_at
        ),
        reverse=True
    )
    return incidents

@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    rec = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record_to_incident(rec, db)
