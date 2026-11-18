import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.schemas import TriageResult, EnrichedContext
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.services.resilience import ResilienceManager
from backend.app.config import settings

logger = logging.getLogger("nexusops.enrichment")

class EnrichmentAgent:
    """
    Agent 2: Context & Policy Enrichment Agent
    Fetches real-time telemetry from mock CRM, Infrastructure, Inventory, and Policy engines.
    Features exponential backoff retries, Chaos Mode handling, caching, and graceful degradation.
    """

    def __init__(self, db: Session, chaos_mode: Optional[bool] = None):
        self.db = db
        self.chaos_mode = settings.chaos_mode if chaos_mode is None else chaos_mode
        self.resilience = ResilienceManager(chaos_mode=self.chaos_mode)

    def run(self, triage: TriageResult) -> EnrichedContext:
        degraded_services: List[str] = []
        total_retries = 0
        crm_data: Dict[str, Any] = {}
        infra_data: Dict[str, Any] = {}
        inventory_data: Dict[str, Any] = {}
        policy_data: Dict[str, Any] = {}

        # 1. CRM Enrichment with Retry & Chaos injection
        for cust_id in triage.entities.customer_ids:
            cache_key = f"crm:{cust_id}"
            cached = self.resilience.get_from_cache(cache_key)
            if cached:
                crm_data[cust_id] = cached
            else:
                data, retries, degraded = self.resilience.execute_with_retry(
                    operation_name=f"CRM_Service_Query_{cust_id}",
                    func=lambda cid=cust_id: EnterpriseSimulator.get_customer_crm(self.db, cid),
                    max_retries=3,
                    base_delay=0.02
                )
                total_retries += retries
                if degraded or not data:
                    degraded_services.append("CRM")
                    crm_data[cust_id] = {
                        "status": "unavailable",
                        "customer_id": cust_id,
                        "fallback_note": "CRM Microservice 503 Gateway Timeout; graceful fallback applied."
                    }
                else:
                    self.resilience.set_in_cache(cache_key, data)
                    crm_data[cust_id] = data

        # Default CRM fallback if none extracted
        if not crm_data:
            crm_data["default"] = {"tier": "Standard", "status": "No specific customer ID extracted"}

        # 2. Infra Telemetry
        for node_id in triage.entities.server_nodes:
            cache_key = f"infra:{node_id}"
            cached = self.resilience.get_from_cache(cache_key)
            if cached:
                infra_data[node_id] = cached
            else:
                data, retries, degraded = self.resilience.execute_with_retry(
                    operation_name=f"Infra_Telemetry_{node_id}",
                    func=lambda nid=node_id: EnterpriseSimulator.get_node_telemetry(self.db, nid),
                    max_retries=2,
                    base_delay=0.02
                )
                total_retries += retries
                if degraded or not data:
                    degraded_services.append("InfraTelemetry")
                    infra_data[node_id] = {"status": "unavailable"}
                else:
                    self.resilience.set_in_cache(cache_key, data)
                    infra_data[node_id] = data

        # 3. Inventory Stock
        for sku in triage.entities.skus:
            cache_key = f"inventory:{sku}"
            cached = self.resilience.get_from_cache(cache_key)
            if cached:
                inventory_data[sku] = cached
            else:
                data, retries, degraded = self.resilience.execute_with_retry(
                    operation_name=f"Inventory_SKU_{sku}",
                    func=lambda s=sku: EnterpriseSimulator.get_inventory_sku(self.db, s),
                    max_retries=2,
                    base_delay=0.02
                )
                total_retries += retries
                if data:
                    self.resilience.set_in_cache(cache_key, data)
                    inventory_data[sku] = data

        # 4. Applicable Policy Rules
        fin_policy = EnterpriseSimulator.get_policy(self.db, "FIN_REFUND_THRESHOLD")
        infra_policy = EnterpriseSimulator.get_policy(self.db, "INFRA_MUTATION_POLICY")
        inv_policy = EnterpriseSimulator.get_policy(self.db, "INVENTORY_ALLOCATION_POLICY")

        policy_data["FIN_REFUND_THRESHOLD"] = fin_policy
        policy_data["INFRA_MUTATION_POLICY"] = infra_policy
        policy_data["INVENTORY_ALLOCATION_POLICY"] = inv_policy

        # Synthesize policy compliance checks
        policy_checks = []
        max_refund = fin_policy["max_auto_approved_amount"] if fin_policy else 100.0
        for amt in triage.entities.financial_amounts:
            if amt > max_refund:
                policy_checks.append(f"Financial amount ${amt:.2f} exceeds auto-approval threshold (${max_refund:.2f}). Requires manager sign-off.")

        for node_id, node_info in infra_data.items():
            if isinstance(node_info, dict) and "prod" in str(node_info.get("cluster", "")).lower():
                policy_checks.append(f"Target node '{node_id}' belongs to production cluster '{node_info.get('cluster')}'. Requires manager sign-off.")

        policy_data["compliance_evaluation"] = policy_checks

        # Formulate agent reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Enriched {len(crm_data)} CRM profiles, {len(infra_data)} infra nodes, and {len(inventory_data)} inventory SKUs.")
        if total_retries > 0:
            reasoning_parts.append(f"Encountered {total_retries} retry attempts during telemetry retrieval.")
        if degraded_services:
            reasoning_parts.append(f"Degraded microservices: {', '.join(degraded_services)} (operating in fallback mode).")
        if policy_checks:
            reasoning_parts.append(f"Policy flags triggered: {len(policy_checks)} conditions requiring human escalation.")

        context = EnrichedContext(
            crm=crm_data,
            infra=infra_data,
            inventory=inventory_data,
            policy=policy_data,
            retry_count=total_retries,
            degraded_services=degraded_services,
            confidence_score=0.92 if not degraded_services else 0.85,
            agent_reasoning=" ".join(reasoning_parts)
        )

        return context
