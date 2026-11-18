import pytest
from backend.app.agents.triage_agent import TriageAgent
from backend.app.models.schemas import SLAPriority, Department
from simulator.scenarios import SCENARIOS, get_scenario_by_id

def test_extract_entities_scenario_sla_breach():
    s = get_scenario_by_id("scenario-sla-breach-250")
    entities = TriageAgent.extract_entities_regex(s["raw_event"])

    assert "CUST-10482" in entities.customer_ids
    assert "ORD-991285" in entities.order_ids or "INC-8921" in entities.order_ids
    assert 250.0 in entities.financial_amounts
    assert "node-eu-prod-04" in entities.server_nodes
    assert "ERR_CLUSTER_NODE_TIMEOUT" in entities.error_codes or "HTTP 503" in entities.error_codes

def test_extract_entities_scenario_vip_bulk_order():
    s = get_scenario_by_id("scenario-vip-bulk-order-conflict")
    entities = TriageAgent.extract_entities_regex(s["raw_event"])

    assert "ORG-ACME" in entities.customer_ids
    assert "ORD-84729" in entities.order_ids
    assert "SKU-SERVER-RACK-99" in entities.skus
    assert 4500.0 in entities.financial_amounts or 112500.0 in entities.financial_amounts

def test_extract_entities_scenario_password_reset():
    s = get_scenario_by_id("scenario-routine-password-reset")
    entities = TriageAgent.extract_entities_regex(s["raw_event"])

    assert "srv-auth-master-01" in entities.server_nodes
    assert "TICKET-77312" in entities.order_ids
    assert len(entities.financial_amounts) == 0

def test_detect_prompt_injection_pattern():
    attack = get_scenario_by_id("scenario-prompt-injection-attack")
    assert TriageAgent.detect_prompt_injection(attack["raw_event"]) is True

    benign = get_scenario_by_id("scenario-routine-password-reset")
    assert TriageAgent.detect_prompt_injection(benign["raw_event"]) is False

def test_triage_agent_full_run_with_injection():
    agent = TriageAgent()
    attack = get_scenario_by_id("scenario-prompt-injection-attack")
    result = agent.run(attack["raw_event"], attack["channel"])

    assert result.prompt_injection_detected is True
    assert result.sla_priority == SLAPriority.CRITICAL
    assert result.routing.primary_department == Department.SECURITY
    assert 10000.0 in result.entities.financial_amounts
    assert "CUST-55120" in result.entities.customer_ids

def test_triage_agent_full_run_sla_breach():
    agent = TriageAgent()
    s = get_scenario_by_id("scenario-sla-breach-250")
    result = agent.run(s["raw_event"], s["channel"])

    assert result.prompt_injection_detected is False
    assert result.sla_priority in (SLAPriority.CRITICAL, SLAPriority.HIGH)
    assert Department.IT in result.routing.departments
    assert Department.FINANCE in result.routing.departments
