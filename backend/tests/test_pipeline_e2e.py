import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.models.database import Base, IncidentRecord, ActionRecord, SimCustomer, SimNode, SimInventory, AuditLogRecord
from backend.app.models.schemas import IncidentCreate, ActionRiskLevel, SLAPriority, Department
from backend.app.agents.orchestrator import NexusOrchestrator
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from simulator.scenarios import get_scenario_by_id

@pytest.fixture
def e2e_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    EnterpriseSimulator.seed_initial_state(db)
    yield db
    db.close()

def test_scenario_1_sla_breach_e2e(e2e_db):
    s = get_scenario_by_id("scenario-sla-breach-250")
    orchestrator = NexusOrchestrator(db=e2e_db, chaos_mode=False)
    incident = orchestrator.process_incident(IncidentCreate(
        title=s["title"],
        raw_event=s["raw_event"],
        channel=s["channel"]
    ))

    assert incident.sla_priority in (SLAPriority.CRITICAL, SLAPriority.HIGH)
    assert len(incident.actions) >= 3

    # Gated financial credit action
    credit_act = next(a for a in incident.actions if a.type == "issue_credit")
    assert credit_act.financial_impact == 250.0
    assert credit_act.requires_approval is True
    assert "FIN_GUARDRAIL" in credit_act.guardrail_trigger

    # Gated prod restart action
    restart_act = next(a for a in incident.actions if a.type == "restart_node")
    assert restart_act.requires_approval is True
    assert "INFRA_GUARDRAIL" in restart_act.guardrail_trigger

    # Safe email dispatch action
    email_act = next(a for a in incident.actions if a.type == "dispatch_email")
    assert email_act.requires_approval is False

    # Execute credit action
    act_rec = e2e_db.query(ActionRecord).filter(ActionRecord.id == credit_act.id).first()
    EnterpriseSimulator.execute_action(e2e_db, act_rec)
    cust = e2e_db.query(SimCustomer).filter(SimCustomer.customer_id == "CUST-10482").first()
    assert cust.credit_balance == 250.0

def test_scenario_2_bulk_order_conflict_e2e(e2e_db):
    s = get_scenario_by_id("scenario-vip-bulk-order-conflict")
    orchestrator = NexusOrchestrator(db=e2e_db)
    incident = orchestrator.process_incident(IncidentCreate(
        title=s["title"],
        raw_event=s["raw_event"],
        channel=s["channel"]
    ))

    assert incident.sla_priority == SLAPriority.HIGH
    hold_act = next(a for a in incident.actions if a.type == "hold_shipment")
    assert hold_act.requires_approval is True
    assert hold_act.payload.get("quantity") == 25

    # Execute shipment hold
    act_rec = e2e_db.query(ActionRecord).filter(ActionRecord.id == hold_act.id).first()
    EnterpriseSimulator.execute_action(e2e_db, act_rec)
    inv = e2e_db.query(SimInventory).filter(SimInventory.sku == "SKU-SERVER-RACK-99").first()
    assert inv.reserved_quantity == 30  # 5 baseline + 25 newly reserved

def test_scenario_3_password_reset_benign_control(e2e_db):
    s = get_scenario_by_id("scenario-routine-password-reset")
    orchestrator = NexusOrchestrator(db=e2e_db)
    incident = orchestrator.process_incident(IncidentCreate(
        title=s["title"],
        raw_event=s["raw_event"],
        channel=s["channel"]
    ))

    assert incident.sla_priority == SLAPriority.LOW
    assert len(incident.actions) == 1
    act = incident.actions[0]
    assert act.type == "reset_credentials"
    assert act.requires_approval is False
    assert act.risk_level == ActionRiskLevel.LOW

def test_scenario_4_prompt_injection_defense_e2e(e2e_db):
    s = get_scenario_by_id("scenario-prompt-injection-attack")
    orchestrator = NexusOrchestrator(db=e2e_db)
    incident = orchestrator.process_incident(IncidentCreate(
        title=s["title"],
        raw_event=s["raw_event"],
        channel=s["channel"]
    ))

    assert incident.triage.prompt_injection_detected is True
    assert incident.sla_priority == SLAPriority.CRITICAL
    assert incident.triage.routing.primary_department == Department.SECURITY

    # Zero unauthorized $10,000 credit actions generated!
    assert not any(a.type == "issue_credit" for a in incident.actions)

    # Quarantined action present
    quarantine_act = next(a for a in incident.actions if a.type == "quarantine_ticket")
    assert quarantine_act.risk_level == ActionRiskLevel.CRITICAL
    assert quarantine_act.requires_approval is True

    # Audit log check
    audit_entries = e2e_db.query(AuditLogRecord).filter(AuditLogRecord.incident_id == incident.id).all()
    assert any("prompt_injection" in a.details_json for a in audit_entries)
