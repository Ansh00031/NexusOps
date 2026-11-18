import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.database import Base
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.agents.triage_agent import TriageAgent
from backend.app.agents.enrichment_agent import EnrichmentAgent
from backend.app.services.resilience import ResilienceManager
from simulator.scenarios import get_scenario_by_id

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    EnterpriseSimulator.seed_initial_state(db)
    yield db
    db.close()

def test_enrichment_normal(db_session):
    s = get_scenario_by_id("scenario-sla-breach-250")
    triage = TriageAgent().run(s["raw_event"], s["channel"])

    agent = EnrichmentAgent(db=db_session, chaos_mode=False)
    context = agent.run(triage)

    # Verify CRM data enriched
    assert "CUST-10482" in context.crm
    assert context.crm["CUST-10482"]["tier"] == "Enterprise VIP"
    assert context.crm["CUST-10482"]["ltv"] == 185000.0

    # Verify Infra telemetry enriched
    assert "node-eu-prod-04" in context.infra
    assert context.infra["node-eu-prod-04"]["status"] == "degraded"
    assert context.infra["node-eu-prod-04"]["cpu_pct"] > 90.0

    # Verify Policy compliance detected breach
    compliance = context.policy.get("compliance_evaluation", [])
    assert any("250.00" in c for c in compliance)
    assert any("production cluster" in c for c in compliance)
    assert len(context.degraded_services) == 0

def test_enrichment_resilience_cache(db_session):
    resilience = ResilienceManager()
    resilience.set_in_cache("test:key", {"status": "ok"})
    cached = resilience.get_from_cache("test:key")
    assert cached == {"status": "ok"}

def test_enrichment_chaos_mode_retry_and_degradation(db_session):
    s = get_scenario_by_id("scenario-sla-breach-250")
    triage = TriageAgent().run(s["raw_event"], s["channel"])

    # Run with Chaos Mode enabled
    agent = EnrichmentAgent(db=db_session, chaos_mode=True)
    context = agent.run(triage)

    # Should have attempted retries
    assert context.retry_count >= 2
    # Even if CRM had transient errors or degraded, pipeline never crashed!
    assert context.infra is not None
    assert "node-eu-prod-04" in context.infra
    assert context.infra["node-eu-prod-04"]["status"] == "degraded"
