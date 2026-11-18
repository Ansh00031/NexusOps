import pytest
import json
import hashlib
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.models.database import (
    Base, SimCustomer, SimNode, SimInventory, SimBillingCredit, ActionRecord, AuditLogRecord
)
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.services.audit_logger import AuditLogger
from backend.app.api.metrics import get_roi_metrics
from backend.app.models.database import IncidentRecord

@pytest.fixture
def sim_db():
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

def test_immutable_audit_log_checksum(sim_db):
    entry = AuditLogger.log(
        db=sim_db,
        incident_id="inc-test-123",
        agent="HumanManager",
        event_type="APPROVED_AND_EXECUTED",
        details={"amount": 250.0, "target": "CUST-10482"},
        action_id="act-test-456"
    )

    assert entry.id.startswith("aud-")
    assert len(entry.checksum) == 64  # SHA256 length

    # Re-calculate chained hash and verify integrity
    computed_hash = AuditLogger.compute_hash(
        record_id=entry.id,
        incident_id=entry.incident_id,
        action_id=entry.action_id,
        agent=entry.agent,
        event_type=entry.event_type,
        details_str=entry.details_json,
        timestamp_iso=entry.timestamp.isoformat(),
        previous_checksum=entry.previous_checksum
    )
    assert entry.checksum == computed_hash

    # Verify complete chain integrity
    is_valid, err, count = AuditLogger.verify_chain_integrity(sim_db)
    assert is_valid is True

def test_stateful_executor_and_rollback_credit(sim_db):
    # Customer baseline
    cust = sim_db.query(SimCustomer).filter(SimCustomer.customer_id == "CUST-10482").first()
    initial_balance = cust.credit_balance

    # Create proposed credit action
    action = ActionRecord(
        id="act-credit-test",
        incident_id="inc-test-1",
        department="FINANCE",
        type="issue_credit",
        target="CUST-10482",
        payload_json=json.dumps({"amount": 250.0, "customer_id": "CUST-10482"}),
        rationale="SLA breach credit",
        financial_impact=250.0,
        risk_level="HIGH",
        reversibility=True,
        rollback_action="reverse_billing_credit",
        status="pending"
    )
    sim_db.add(action)
    sim_db.commit()

    # 1. Execute
    exec_res = EnterpriseSimulator.execute_action(sim_db, action)
    assert exec_res["success"] is True
    assert action.status == "executed-simulated"

    # Verify DB updated
    sim_db.refresh(cust)
    assert cust.credit_balance == initial_balance + 250.0

    credit_rec = sim_db.query(SimBillingCredit).filter(SimBillingCredit.customer_id == "CUST-10482").first()
    assert credit_rec is not None
    assert credit_rec.amount == 250.0
    assert credit_rec.status == "applied"

    # 2. Rollback
    rb_res = EnterpriseSimulator.rollback_action(sim_db, action)
    assert rb_res["success"] is True
    assert action.status == "rolled-back"

    # Verify DB restored
    sim_db.refresh(cust)
    assert cust.credit_balance == initial_balance
    sim_db.refresh(credit_rec)
    assert credit_rec.status == "reversed"

def test_stateful_executor_and_rollback_node_restart(sim_db):
    node = sim_db.query(SimNode).filter(SimNode.node_id == "node-eu-prod-04").first()
    assert node.status == "degraded"

    action = ActionRecord(
        id="act-node-restart",
        incident_id="inc-test-2",
        department="IT",
        type="restart_node",
        target="node-eu-prod-04",
        payload_json="{}",
        rationale="Graceful cluster restart",
        financial_impact=0.0,
        risk_level="HIGH",
        reversibility=True,
        rollback_action="revert_node_state",
        status="pending"
    )
    sim_db.add(action)
    sim_db.commit()

    # Execute
    EnterpriseSimulator.execute_action(sim_db, action)
    sim_db.refresh(node)
    assert node.status == "healthy"
    assert node.cpu_pct < 50.0

    # Rollback
    EnterpriseSimulator.rollback_action(sim_db, action)
    sim_db.refresh(node)
    assert node.status == "degraded"

def test_roi_metrics_calculation(sim_db):
    # Seed an incident and rejected action
    inc = IncidentRecord(
        id="inc-metrics-1",
        title="Outage resolution",
        raw_event="outage text",
        channel="email",
        status="resolved",
        sla_priority="CRITICAL",
        financial_impact=250.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        triage_json='{"prompt_injection_detected": true}'
    )
    sim_db.add(inc)

    act_rejected = ActionRecord(
        id="act-rej-1",
        incident_id="inc-metrics-1",
        department="FINANCE",
        type="issue_credit",
        target="CUST-10482",
        payload_json="{}",
        rationale="unauthorized",
        financial_impact=500.0,
        risk_level="HIGH",
        status="rejected"
    )
    sim_db.add(act_rejected)
    sim_db.commit()

    metrics = get_roi_metrics(sim_db)
    assert metrics.tickets_resolved == 1
    assert metrics.hours_saved >= 1.0
    # $500 rejected action + $10000 injection attempt prevented
    assert metrics.dollars_protected == 10500.0
