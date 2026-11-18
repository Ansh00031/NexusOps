import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.app.models.database import get_db, ActionRecord, IncidentRecord
from backend.app.models.schemas import ActionProposed, ApprovalRequest, ActionStatus, Department, ActionRiskLevel
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.services.audit_logger import AuditLogger

router = APIRouter(prefix="/api/actions", tags=["actions"])

def action_record_to_schema(a: ActionRecord) -> ActionProposed:
    return ActionProposed(
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
    )

def check_and_update_incident_status(db: Session, incident_id: str):
    """If all actions are executed or resolved, update incident status."""
    actions = db.query(ActionRecord).filter(ActionRecord.incident_id == incident_id).all()
    if actions:
        all_resolved = all(a.status in ("executed-simulated", "rejected", "rolled-back") for a in actions)
        inc = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if inc:
            if all_resolved:
                inc.status = "resolved"
            else:
                inc.status = "resolving"
            inc.updated_at = datetime.utcnow()
            db.commit()

@router.post("/{action_id}/approve", response_model=ActionProposed)
def approve_action(
    action_id: str,
    req: Optional[ApprovalRequest] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Approve an action in the Human-in-the-Loop workflow.
    Executes the action against the stateful enterprise simulator.
    """
    act = db.query(ActionRecord).filter(ActionRecord.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Action not found")

    if act.status in ("executed-simulated", "approved"):
        raise HTTPException(status_code=400, detail="Action is already executed")

    comment = req.comment if req else None
    act.manager_comment = comment

    # Execute against stateful simulator
    exec_result = EnterpriseSimulator.execute_action(db, act)

    # Log immutable audit
    AuditLogger.log(
        db=db,
        incident_id=act.incident_id,
        action_id=act.id,
        agent="HumanOperationsManager",
        event_type="APPROVED_AND_EXECUTED",
        details={
            "action_type": act.type,
            "target": act.target,
            "manager_comment": comment,
            "financial_impact": act.financial_impact,
            "execution_result": exec_result
        }
    )

    check_and_update_incident_status(db, act.incident_id)
    return action_record_to_schema(act)

@router.post("/{action_id}/reject", response_model=ActionProposed)
def reject_action(
    action_id: str,
    req: Optional[ApprovalRequest] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Reject a proposed action with manager rationale.
    """
    act = db.query(ActionRecord).filter(ActionRecord.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Action not found")

    act.status = "rejected"
    comment = req.comment if req else "Rejected by human operations manager."
    act.manager_comment = comment
    db.commit()

    AuditLogger.log(
        db=db,
        incident_id=act.incident_id,
        action_id=act.id,
        agent="HumanOperationsManager",
        event_type="REJECTED",
        details={"action_type": act.type, "manager_comment": comment}
    )

    check_and_update_incident_status(db, act.incident_id)
    return action_record_to_schema(act)

@router.post("/approve-safe", response_model=List[ActionProposed])
def approve_safe_actions(
    incident_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    One-click approval for all safe / low-risk actions on an incident.
    """
    actions = db.query(ActionRecord).filter(
        ActionRecord.incident_id == incident_id,
        ActionRecord.requires_approval == False,
        ActionRecord.status == "pending"
    ).all()

    executed = []
    for act in actions:
        EnterpriseSimulator.execute_action(db, act)
        AuditLogger.log(
            db=db,
            incident_id=incident_id,
            action_id=act.id,
            agent="NexusOrchestratorAutoApprove",
            event_type="SAFE_ACTION_AUTO_EXECUTED",
            details={"action_type": act.type, "target": act.target}
        )
        executed.append(action_record_to_schema(act))

    check_and_update_incident_status(db, incident_id)
    return executed

@router.post("/{action_id}/rollback", response_model=ActionProposed)
def rollback_action(
    action_id: str,
    db: Session = Depends(get_db)
):
    """
    Rollback an executed simulated action to revert simulator state.
    """
    act = db.query(ActionRecord).filter(ActionRecord.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Action not found")

    if act.status != "executed-simulated":
        raise HTTPException(status_code=400, detail="Only executed actions can be rolled back.")

    rollback_details = EnterpriseSimulator.rollback_action(db, act)

    AuditLogger.log(
        db=db,
        incident_id=act.incident_id,
        action_id=act.id,
        agent="HumanOperationsManager",
        event_type="ROLLBACK",
        details=rollback_details
    )

    check_and_update_incident_status(db, act.incident_id)
    return action_record_to_schema(act)
