from typing import Tuple, Optional
from backend.app.models.schemas import ActionProposed, ActionRiskLevel, EnrichedContext

class GuardrailEngine:
    """
    Hard programmatic business guardrails that govern AI proposed actions.
    Ensures no LLM hallucinations or prompt injection attacks can bypass financial
    ceilings or destructive infrastructure operations.
    """

    MAX_AUTO_CREDIT_AMOUNT = 100.0

    @classmethod
    def evaluate(cls, action: ActionProposed, context: Optional[EnrichedContext] = None, prompt_injection: bool = False) -> Tuple[bool, Optional[str], ActionRiskLevel]:
        """
        Evaluates an action against strict corporate policies.
        Returns: (requires_approval: bool, guardrail_trigger: Optional[str], adjusted_risk: ActionRiskLevel)
        """
        # Guardrail 1: Security Quarantine for Prompt Injection
        if prompt_injection:
            return True, "SECURITY_GUARDRAIL: Adversarial prompt injection detected. All automated execution blocked.", ActionRiskLevel.CRITICAL

        # Guardrail 2: Financial Threshold ($100 max auto-approval)
        if action.financial_impact > cls.MAX_AUTO_CREDIT_AMOUNT:
            return True, f"FIN_GUARDRAIL: Financial impact ${action.financial_impact:.2f} exceeds auto-approval ceiling of ${cls.MAX_AUTO_CREDIT_AMOUNT:.2f}.", ActionRiskLevel.HIGH

        if action.type in ("issue_credit", "refund_billing", "sla_credit"):
            if action.financial_impact > cls.MAX_AUTO_CREDIT_AMOUNT:
                return True, f"FIN_GUARDRAIL: Billing credit ${action.financial_impact:.2f} requires Operations Manager approval.", ActionRiskLevel.HIGH
            elif action.financial_impact > 0:
                # Check if customer is VIP in context
                if context and context.crm:
                    for cid, cinfo in context.crm.items():
                        if isinstance(cinfo, dict) and "vip" in str(cinfo.get("tier", "")).lower():
                            return True, f"VIP_POLICY: Customer '{cid}' is VIP tier ({cinfo.get('tier')}). Credit adjustments require verification.", ActionRiskLevel.MEDIUM

        # Guardrail 3: Production Infrastructure Mutations
        if action.type in ("restart_node", "restart_worker_node", "reboot_host", "scale_instance"):
            target_lower = action.target.lower()
            # If target or context cluster contains "prod"
            is_prod = "prod" in target_lower
            if context and context.infra:
                for nid, ninfo in context.infra.items():
                    if isinstance(ninfo, dict) and "prod" in str(ninfo.get("cluster", "")).lower():
                        is_prod = True
            if is_prod:
                return True, f"INFRA_GUARDRAIL: Target '{action.target}' is in a production cluster. Restarts require human verification.", ActionRiskLevel.HIGH

        # Guardrail 4: Inventory Deficit / Critical Stock
        if action.type in ("hold_shipment", "reserve_inventory", "fulfill_order"):
            if context and context.inventory:
                for sku, inv_info in context.inventory.items():
                    if isinstance(inv_info, dict):
                        avail = inv_info.get("available_quantity", inv_info.get("stock_quantity", 0))
                        requested = action.payload.get("quantity", 0)
                        if requested > avail:
                            return True, f"INVENTORY_GUARDRAIL: Requested {requested} exceeds available inventory {avail} for SKU {sku}.", ActionRiskLevel.HIGH

        # Safe Actions (low risk, <= $100, benign)
        if action.risk_level == ActionRiskLevel.LOW and action.financial_impact <= cls.MAX_AUTO_CREDIT_AMOUNT:
            return False, None, ActionRiskLevel.LOW

        # Default fallback: err on caution
        return True, "STANDARD_REVIEW: Action requires operational sign-off.", action.risk_level
