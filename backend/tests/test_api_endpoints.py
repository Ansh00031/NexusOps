import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.models.database import Base, get_db
from backend.app.services.enterprise_simulator import EnterpriseSimulator

from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite with StaticPool so all sessions share the tables
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base.metadata.create_all(bind=test_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    db = TestingSessionLocal()
    EnterpriseSimulator.seed_initial_state(db)
    db.close()

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_incident_sla_breach():
    payload = {
        "title": "Test SLA Breach",
        "raw_event": "",
        "channel": "email",
        "scenario_id": "scenario-sla-breach-250"
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "inc-" in data["id"]
    assert data["sla_priority"] in ("CRITICAL", "HIGH")
    assert len(data["actions"]) >= 3
    assert len(data["reasoning_timeline"]) >= 3

def test_list_incidents():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) >= 1

def test_approve_and_rollback_action():
    # 1. Ingest incident
    create_res = client.post("/api/incidents", json={
        "title": "Test Action Lifecycle",
        "raw_event": "",
        "scenario_id": "scenario-sla-breach-250"
    })
    incident = create_res.json()
    actions = incident["actions"]

    # Pick the issue_credit action
    credit_action = next((a for a in actions if a["type"] == "issue_credit"), actions[0])
    act_id = credit_action["id"]

    # 2. Approve action
    approve_res = client.post(f"/api/actions/{act_id}/approve", json={"comment": "Approved for VIP retention"})
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["status"] == "executed-simulated"
    assert approved_data["execution_result"] is not None

    # 3. Rollback action
    rollback_res = client.post(f"/api/actions/{act_id}/rollback")
    assert rollback_res.status_code == 200
    rolled_back_data = rollback_res.json()
    assert rolled_back_data["status"] == "rolled-back"

def test_chaos_mode_toggle():
    res1 = client.post("/api/simulator/chaos", json={"enabled": True})
    assert res1.status_code == 200
    assert res1.json()["chaos_mode"] is True

    res2 = client.post("/api/simulator/chaos", json={"enabled": False})
    assert res2.status_code == 200
    assert res2.json()["chaos_mode"] is False

def test_metrics_roi():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert "hours_saved" in metrics
    assert "dollars_protected" in metrics
    assert "mean_time_to_resolution_sec" in metrics
