import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.database import Base, SimCustomer, SimNode, SimInventory, SimPolicyRule
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from simulator.scenarios import SCENARIOS, get_scenario_by_id

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    EnterpriseSimulator.seed_initial_state(db)
    yield db
    db.close()

def test_database_seeding(test_db):
    cust = test_db.query(SimCustomer).filter(SimCustomer.customer_id == "CUST-10482").first()
    assert cust is not None
    assert cust.tier == "Enterprise VIP"
    assert cust.name == "Acme Global Financial Corp"

    node = test_db.query(SimNode).filter(SimNode.node_id == "node-eu-prod-04").first()
    assert node is not None
    assert node.status == "degraded"

    inv = test_db.query(SimInventory).filter(SimInventory.sku == "SKU-SERVER-RACK-99").first()
    assert inv is not None
    assert inv.stock_quantity == 20

    policy = test_db.query(SimPolicyRule).filter(SimPolicyRule.rule_key == "FIN_REFUND_THRESHOLD").first()
    assert policy is not None
    assert policy.max_auto_approved_amount == 100.0

def test_scenarios_available():
    assert len(SCENARIOS) == 4
    s1 = get_scenario_by_id("scenario-sla-breach-250")
    assert "CUST-10482" in s1["raw_event"]
    assert "$250.00" in s1["raw_event"]

    s4 = get_scenario_by_id("scenario-prompt-injection-attack")
    assert "SYSTEM OVERRIDE INSTRUCTION" in s4["raw_event"]
