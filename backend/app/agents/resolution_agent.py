import uuid
import logging
from typing import List, Dict, Any, Optional
from backend.app.models.schemas import (
    TriageResult, EnrichedContext, ActionProposed, ActionRiskLevel, ActionStatus, Department, ResolutionPlan
)
from backend.app.services.guardrails import GuardrailEngine

logger = logging.getLogger("nexusops.resolution")

class ResolutionAgent:
    """
    Agent 3: Resolution & Action Agent
    Drafts cross-departmental operational actions and evaluates them against
    hard programmatic business guardrails.
    """

    def run(self, triage: TriageResult, context: EnrichedContext) -> ResolutionPlan:
        actions: List[ActionProposed] = []

        # Case 1: Prompt Injection Quarantine
        if triage.prompt_injection_detected:
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            sec_action = ActionProposed(
                id=act_id,
                department=Department.SECURITY,
                type="quarantine_ticket",
                target="untrusted_payload_sender",
                payload={"quarantine_reason": triage.security_warning or "Adversarial prompt injection attempt"},
                rationale="Prompt injection detected attempting administrative bypass and financial manipulation. Security quarantine enforced.",
                financial_impact=0.0,
                risk_level=ActionRiskLevel.CRITICAL,
                reversibility=True,
                rollback_action="unquarantine_ticket",
                status=ActionStatus.PENDING,
                requires_approval=True,
                guardrail_trigger="SECURITY_GUARDRAIL: Malicious prompt injection quarantined."
            )
            actions.append(sec_action)

        # Case 2: Infra Outage / Degraded Node
        elif any("node" in n or "srv" in n for n in triage.entities.server_nodes) and any("503" in e or "TIMEOUT" in e for e in triage.entities.error_codes):
            for node_id in triage.entities.server_nodes:
                act_id = f"act-{uuid.uuid4().hex[:8]}"
                restart_action = ActionProposed(
                    id=act_id,
                    department=Department.IT,
                    type="restart_node",
                    target=node_id,
                    payload={"drain_connections": True, "grace_period_sec": 30},
                    rationale=f"Service node {node_id} reported degraded telemetry with 503 errors. Graceful cluster restart required.",
                    financial_impact=0.0,
                    risk_level=ActionRiskLevel.HIGH,
                    reversibility=True,
                    rollback_action="revert_node_state",
                    status=ActionStatus.PENDING
                )
                actions.append(restart_action)

            # Check financial refund demand
            for amt in triage.entities.financial_amounts:
                cust_target = triage.entities.customer_ids[0] if triage.entities.customer_ids else "UNKNOWN_CUSTOMER"
                act_id = f"act-{uuid.uuid4().hex[:8]}"
                credit_action = ActionProposed(
                    id=act_id,
                    department=Department.FINANCE,
                    type="issue_credit",
                    target=cust_target,
                    payload={"amount": amt, "customer_id": cust_target, "reason": "SLA Breach Outage Compensation"},
                    rationale=f"Customer requested ${amt:.2f} SLA billing credit due to cluster downtime.",
                    financial_impact=amt,
                    risk_level=ActionRiskLevel.HIGH if amt > 100.0 else ActionRiskLevel.LOW,
                    reversibility=True,
                    rollback_action="reverse_billing_credit",
                    status=ActionStatus.PENDING
                )
                actions.append(credit_action)

            # CRM Notification dispatch (Safe action)
            cust_target = triage.entities.customer_ids[0] if triage.entities.customer_ids else "CUSTOMER_DESK"
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            notify_action = ActionProposed(
                id=act_id,
                department=Department.CRM,
                type="dispatch_email",
                target=cust_target,
                payload={"template": "outage_remediation_update", "recipient": cust_target},
                rationale="Dispatch automated incident triage notification and executive acknowledgment.",
                financial_impact=0.0,
                risk_level=ActionRiskLevel.LOW,
                reversibility=False,
                rollback_action=None,
                status=ActionStatus.PENDING
            )
            actions.append(notify_action)

        # Case 3: Bulk Order / Inventory Conflict
        elif triage.entities.skus or any("order" in o.lower() for o in triage.entities.order_ids):
            sku_target = triage.entities.skus[0] if triage.entities.skus else "SKU-SERVER-RACK-99"
            cust_target = triage.entities.customer_ids[0] if triage.entities.customer_ids else "VIP_CUSTOMER"

            # Check quantity
            order_amount = max(triage.entities.financial_amounts) if triage.entities.financial_amounts else 112500.0
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            hold_action = ActionProposed(
                id=act_id,
                department=Department.INVENTORY,
                type="hold_shipment",
                target=sku_target,
                payload={"sku": sku_target, "quantity": 25, "customer_id": cust_target, "order_value": order_amount},
                rationale=f"Order exceeds immediate stock. Hold shipment, reserve 20 available units, and expedite procurement for remainder.",
                financial_impact=order_amount,
                risk_level=ActionRiskLevel.HIGH,
                reversibility=True,
                rollback_action="unreserve_inventory",
                status=ActionStatus.PENDING
            )
            actions.append(hold_action)

            # CRM VIP Logistics notification
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            vip_action = ActionProposed(
                id=act_id,
                department=Department.CRM,
                type="dispatch_email",
                target=cust_target,
                payload={"template": "vip_expedited_fulfillment", "customer_id": cust_target},
                rationale=f"Notify VIP account executive regarding partial stock allocation and air shipping status.",
                financial_impact=0.0,
                risk_level=ActionRiskLevel.LOW,
                reversibility=False,
                rollback_action=None,
                status=ActionStatus.PENDING
            )
            actions.append(vip_action)

        # Case 4: Routine Password / Access Token
        elif "password" in triage.intent.lower() or "iam" in triage.intent.lower() or any("srv-auth" in n for n in triage.entities.server_nodes):
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            reset_action = ActionProposed(
                id=act_id,
                department=Department.IT,
                type="reset_credentials",
                target="srv-auth-master-01",
                payload={"duration_hours": 24, "user_id": "EMP-4491"},
                rationale="Generate temporary 24-hour IAM access token following verified Monday rotation lockout.",
                financial_impact=0.0,
                risk_level=ActionRiskLevel.LOW,
                reversibility=True,
                rollback_action="revoke_credentials",
                status=ActionStatus.PENDING
            )
            actions.append(reset_action)

        # Fallback General Action
        else:
            act_id = f"act-{uuid.uuid4().hex[:8]}"
            gen_action = ActionProposed(
                id=act_id,
                department=Department.CRM,
                type="update_ticket",
                target="CRM-GENERAL",
                payload={"note": triage.executive_summary},
                rationale="Log operational event into central queue.",
                financial_impact=0.0,
                risk_level=ActionRiskLevel.LOW,
                reversibility=True,
                rollback_action=None,
                status=ActionStatus.PENDING
            )
            actions.append(gen_action)

        # Apply Hard Guardrail Evaluation to every action
        auto_count = 0
        req_count = 0
        overall_risk = ActionRiskLevel.LOW

        for action in actions:
            req_approval, trigger, adj_risk = GuardrailEngine.evaluate(
                action=action,
                context=context,
                prompt_injection=triage.prompt_injection_detected
            )
            action.requires_approval = req_approval
            action.guardrail_trigger = trigger
            action.risk_level = adj_risk

            if req_approval:
                req_count += 1
            else:
                auto_count += 1

            if adj_risk == ActionRiskLevel.CRITICAL:
                overall_risk = ActionRiskLevel.CRITICAL
            elif adj_risk == ActionRiskLevel.HIGH and overall_risk != ActionRiskLevel.CRITICAL:
                overall_risk = ActionRiskLevel.HIGH
            elif adj_risk == ActionRiskLevel.MEDIUM and overall_risk not in (ActionRiskLevel.CRITICAL, ActionRiskLevel.HIGH):
                overall_risk = ActionRiskLevel.MEDIUM

        plan = ResolutionPlan(
            actions=actions,
            overall_risk=overall_risk,
            auto_approvable_count=auto_count,
            requires_approval_count=req_count,
            agent_reasoning=f"Synthesized {len(actions)} cross-functional actions ({auto_count} safe/auto-approvable, {req_count} gated by HITL guardrails)."
        )

        return plan
