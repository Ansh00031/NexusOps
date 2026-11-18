import pytest
from backend.app.models.schemas import ActionProposed, ActionRiskLevel, ActionStatus, Department, EnrichedContext
from backend.app.services.guardrails import GuardrailEngine
from backend.app.agents.triage_agent import TriageAgent
from backend.app.agents.resolution_agent import ResolutionAgent
from simulator.scenarios import get_scenario_by_id

def test_guardrail_financial_threshold_100_vs_101():
    # Action with $100.00
    safe_action = ActionProposed(
        id="act-100",
        department=Department.FINANCE,
        type="issue_credit",
        target="CUST-STANDARD",
        payload={"amount": 100.0},
        rationale="Small goodwill adjustment",
        financial_impact=100.0,
        risk_level=ActionRiskLevel.LOW,
        reversibility=True,
        status=ActionStatus.PENDING
    )
    req, trigger, risk = GuardrailEngine.evaluate(safe_action)
    assert req is False
    assert trigger is None

    # Action with $100.01 (exceeds threshold)
    unsafe_action = ActionProposed(
        id="act-101",
        department=Department.FINANCE,
        type="issue_credit",
        target="CUST-STANDARD",
        payload={"amount": 100.01},
        rationale="Exceeds goodwill threshold",
        financial_impact=100.01,
        risk_level=ActionRiskLevel.LOW,
        reversibility=True,
        status=ActionStatus.PENDING
    )
    req, trigger, risk = GuardrailEngine.evaluate(unsafe_action)
    assert req is True
    assert "FIN_GUARDRAIL" in trigger
    assert risk in (ActionRiskLevel.HIGH, ActionRiskLevel.MEDIUM)

def test_guardrail_production_node_mutation():
    prod_action = ActionProposed(
        id="act-prod",
        department=Department.IT,
        type="restart_node",
        target="node-eu-prod-04",
        payload={"drain": True},
        rationale="Restart production node",
        financial_impact=0.0,
        risk_level=ActionRiskLevel.LOW,
        reversibility=True,
        status=ActionStatus.PENDING
    )
    req, trigger, risk = GuardrailEngine.evaluate(prod_action)
    assert req is True
    assert "INFRA_GUARDRAIL" in trigger
    assert risk == ActionRiskLevel.HIGH

def test_guardrail_prompt_injection_lockdown():
    any_action = ActionProposed(
        id="act-injection",
        department=Department.FINANCE,
        type="issue_credit",
        target="CUST-55120",
        payload={"amount": 10000.0},
        rationale="Fake payout",
        financial_impact=10000.0,
        risk_level=ActionRiskLevel.LOW,
        reversibility=True,
        status=ActionStatus.PENDING
    )
    req, trigger, risk = GuardrailEngine.evaluate(any_action, prompt_injection=True)
    assert req is True
    assert "SECURITY_GUARDRAIL" in trigger
    assert risk == ActionRiskLevel.CRITICAL

def test_resolution_agent_sla_breach_actions():
    s = get_scenario_by_id("scenario-sla-breach-250")
    triage = TriageAgent().run(s["raw_event"], s["channel"])
    context = EnrichedContext(
        crm={"CUST-10482": {"tier": "Enterprise VIP"}},
        infra={"node-eu-prod-04": {"cluster": "prod-eu-west-cluster-alpha", "status": "degraded"}}
    )
    agent = ResolutionAgent()
    plan = agent.run(triage, context)

    assert len(plan.actions) >= 3
    # Look for $250 credit action
    credit_act = next((a for a in plan.actions if a.type == "issue_credit"), None)
    assert credit_act is not None
    assert credit_act.financial_impact == 250.0
    assert credit_act.requires_approval is True
    assert "FIN_GUARDRAIL" in credit_act.guardrail_trigger

    # Look for restart action
    restart_act = next((a for a in plan.actions if a.type == "restart_node"), None)
    assert restart_act is not None
    assert restart_act.requires_approval is True
    assert "INFRA_GUARDRAIL" in restart_act.guardrail_trigger

    # Look for safe notification email action
    email_act = next((a for a in plan.actions if a.type == "dispatch_email"), None)
    assert email_act is not None
    assert email_act.requires_approval is False

def test_resolution_agent_routine_password_safe():
    s = get_scenario_by_id("scenario-routine-password-reset")
    triage = TriageAgent().run(s["raw_event"], s["channel"])
    context = EnrichedContext()
    agent = ResolutionAgent()
    plan = agent.run(triage, context)

    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.type == "reset_credentials"
    assert action.requires_approval is False
    assert action.risk_level == ActionRiskLevel.LOW
