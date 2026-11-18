from __future__ import annotations
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.database import (
    SimCustomer, SimNode, SimInventory, SimBillingCredit, SimPolicyRule, ActionRecord
)

def sanitize_lookup_term(val: str, max_len: int = 64) -> str:
    """Sanitize lookup strings against wildcard injection and length overflow."""
    if not val:
        return ""
    # Strip wildcards and control characters
    sanitized = val.replace("%", "").replace("_", "").replace("\\", "").strip()
    return sanitized[:max_len]

class EnterpriseSimulator:
    """
    Stateful Enterprise Simulator
    Maintains simulated production state (CRM, Infrastructure, Inventory, Billing, Policies)
    and executes or rolls back approved actions safely without touching real external systems.
    """

    @staticmethod
    def seed_initial_state(db: Session):
        """Seed deterministic enterprise state if empty."""
        # 1. Customers
        if not db.query(SimCustomer).first():
            customers = [
                SimCustomer(
                    customer_id="CUST-10482",
                    name="Acme Global Financial Corp",
                    tier="Enterprise VIP",
                    ltv=185000.0,
                    credit_balance=0.0,
                    sla_level="99.99% Tier-1 Mission Critical SLA",
                    churn_risk="Low",
                    status="Active"
                ),
                SimCustomer(
                    customer_id="ORG-ACME",
                    name="Acme Systems Europe",
                    tier="VIP",
                    ltv=95000.0,
                    credit_balance=50.0,
                    sla_level="99.95% High-Priority SLA",
                    churn_risk="Medium",
                    status="Active"
                ),
                SimCustomer(
                    customer_id="CUST-55120",
                    name="BetaLogistics Tech",
                    tier="Standard",
                    ltv=12000.0,
                    credit_balance=0.0,
                    sla_level="99.0% Standard SLA",
                    churn_risk="Low",
                    status="Active"
                ),
            ]
            db.add_all(customers)

        # 2. Infrastructure Nodes
        if not db.query(SimNode).first():
            nodes = [
                SimNode(
                    node_id="node-eu-prod-04",
                    cluster="prod-eu-west-cluster-alpha",
                    status="degraded",
                    cpu_pct=98.4,
                    memory_pct=92.1,
                    last_error="ERR_CLUSTER_NODE_TIMEOUT: High memory pressure causing 503 worker dropouts",
                    last_restarted_at=datetime.utcnow()
                ),
                SimNode(
                    node_id="node-us-east-01",
                    cluster="prod-us-east-cluster-primary",
                    status="healthy",
                    cpu_pct=42.1,
                    memory_pct=58.0,
                    last_error=None,
                    last_restarted_at=datetime.utcnow()
                ),
                SimNode(
                    node_id="srv-auth-master-01",
                    cluster="iam-cluster-global",
                    status="healthy",
                    cpu_pct=21.0,
                    memory_pct=36.0,
                    last_error=None,
                    last_restarted_at=datetime.utcnow()
                )
            ]
            db.add_all(nodes)

        # 3. Inventory SKUs
        if not db.query(SimInventory).first():
            inventory = [
                SimInventory(
                    sku="SKU-SERVER-RACK-99",
                    name="Enterprise Quantum 4U Server Rack Unit",
                    stock_quantity=20,
                    reserved_quantity=5,
                    unit_price=4500.0,
                    min_threshold=10
                ),
                SimInventory(
                    sku="SKU-ROUTER-PRO",
                    name="UltraGigabit Core Switch Layer-3",
                    stock_quantity=150,
                    reserved_quantity=20,
                    unit_price=890.0,
                    min_threshold=25
                ),
                SimInventory(
                    sku="SKU-SFP-FIBER-10G",
                    name="10G SFP+ Optical Transceiver Module",
                    stock_quantity=500,
                    reserved_quantity=50,
                    unit_price=85.0,
                    min_threshold=100
                )
            ]
            db.add_all(inventory)

        # 4. Policy Rules
        if not db.query(SimPolicyRule).first():
            policies = [
                SimPolicyRule(
                    rule_key="FIN_REFUND_THRESHOLD",
                    category="FINANCE",
                    max_auto_approved_amount=100.0,
                    description="Customer credits or SLA refunds exceeding $100.00 require human manager approval.",
                    requires_approval_conditions=json.dumps(["amount > 100.0", "customer_tier == 'VIP'"])
                ),
                SimPolicyRule(
                    rule_key="INFRA_MUTATION_POLICY",
                    category="IT",
                    max_auto_approved_amount=0.0,
                    description="Restarting production nodes on VIP clusters or staging nodes with high active traffic requires human confirmation.",
                    requires_approval_conditions=json.dumps(["cluster.startswith('prod')", "target.contains('prod')"])
                ),
                SimPolicyRule(
                    rule_key="INVENTORY_ALLOCATION_POLICY",
                    category="INVENTORY",
                    max_auto_approved_amount=5000.0,
                    description="Bulk orders depleting inventory below min_threshold require operations manager sign-off.",
                    requires_approval_conditions=json.dumps(["stock_remaining < min_threshold"])
                )
            ]
            db.add_all(policies)

        db.commit()

    @staticmethod
    def get_customer_crm(db: Session, customer_id: str) -> Optional[Dict[str, Any]]:
        clean_id = sanitize_lookup_term(customer_id)
        if not clean_id:
            return None
        cust = db.query(SimCustomer).filter(SimCustomer.customer_id == clean_id).first()
        if not cust:
            # Fallback exact or substring match using sanitized term
            cust = db.query(SimCustomer).filter(SimCustomer.customer_id.ilike(f"%{clean_id}%")).first()
        if cust:
            return {
                "customer_id": cust.customer_id,
                "name": cust.name,
                "tier": cust.tier,
                "ltv": cust.ltv,
                "credit_balance": cust.credit_balance,
                "sla_level": cust.sla_level,
                "churn_risk": cust.churn_risk,
                "status": cust.status
            }
        return None

    @staticmethod
    def get_node_telemetry(db: Session, node_id: str) -> Optional[Dict[str, Any]]:
        clean_id = sanitize_lookup_term(node_id)
        if not clean_id:
            return None
        node = db.query(SimNode).filter(SimNode.node_id == clean_id).first()
        if not node:
            node = db.query(SimNode).filter(SimNode.node_id.ilike(f"%{clean_id}%")).first()
        if node:
            return {
                "node_id": node.node_id,
                "cluster": node.cluster,
                "status": node.status,
                "cpu_pct": node.cpu_pct,
                "memory_pct": node.memory_pct,
                "last_error": node.last_error,
                "last_restarted_at": node.last_restarted_at.isoformat() if node.last_restarted_at else None
            }
        return None

    @staticmethod
    def get_inventory_sku(db: Session, sku: str) -> Optional[Dict[str, Any]]:
        clean_sku = sanitize_lookup_term(sku)
        if not clean_sku:
            return None
        item = db.query(SimInventory).filter(SimInventory.sku == clean_sku).first()
        if not item:
            item = db.query(SimInventory).filter(SimInventory.sku.ilike(f"%{clean_sku}%")).first()
        if item:
            return {
                "sku": item.sku,
                "name": item.name,
                "stock_quantity": item.stock_quantity,
                "reserved_quantity": item.reserved_quantity,
                "available_quantity": item.stock_quantity - item.reserved_quantity,
                "unit_price": item.unit_price,
                "min_threshold": item.min_threshold
            }
        return None

    @staticmethod
    def get_policy(db: Session, rule_key: str) -> Optional[Dict[str, Any]]:
        rule = db.query(SimPolicyRule).filter(SimPolicyRule.rule_key == rule_key).first()
        if rule:
            return {
                "rule_key": rule.rule_key,
                "category": rule.category,
                "max_auto_approved_amount": rule.max_auto_approved_amount,
                "description": rule.description
            }
        return None

    @staticmethod
    def execute_action(db: Session, action: ActionRecord) -> Dict[str, Any]:
        """
        Execute an approved action against the stateful enterprise simulator.
        Returns execution result details.
        """
        payload = json.loads(action.payload_json or "{}")
        action_type = action.type
        target = action.target

        execution_details = {
            "executed_at": datetime.utcnow().isoformat(),
            "target": target,
            "action_type": action_type,
            "success": True,
            "simulated": True
        }

        if action_type in ("restart_node", "restart_worker_node"):
            node = db.query(SimNode).filter(SimNode.node_id == target).first()
            if not node:
                node = db.query(SimNode).filter(SimNode.node_id.ilike(f"%{target}%")).first()
            if node:
                prev_status = node.status
                node.status = "healthy"
                node.cpu_pct = 24.5
                node.memory_pct = 38.0
                node.last_error = None
                node.last_restarted_at = datetime.utcnow()
                execution_details["previous_status"] = prev_status
                execution_details["new_status"] = "healthy"
                execution_details["message"] = f"Simulated node {node.node_id} gracefully restarted and telemetry verified healthy."

        elif action_type in ("issue_credit", "refund_billing", "sla_credit"):
            amount = float(payload.get("amount", action.financial_impact))
            customer_id = payload.get("customer_id", target)
            cust = db.query(SimCustomer).filter(SimCustomer.customer_id == customer_id).first()
            if not cust:
                cust = db.query(SimCustomer).filter(SimCustomer.customer_id.ilike(f"%{customer_id}%")).first()

            credit_id = f"CRED-{uuid.uuid4().hex[:8].upper()}"
            credit = SimBillingCredit(
                credit_id=credit_id,
                customer_id=cust.customer_id if cust else customer_id,
                amount=amount,
                reason=action.rationale,
                status="applied",
                created_at=datetime.utcnow()
            )
            db.add(credit)

            if cust:
                cust.credit_balance += amount
                execution_details["customer_new_credit_balance"] = cust.credit_balance

            execution_details["credit_id"] = credit_id
            execution_details["amount_credited"] = amount
            execution_details["message"] = f"Simulated billing credit ${amount:.2f} issued to customer {customer_id}."

        elif action_type in ("hold_shipment", "reserve_inventory"):
            sku = payload.get("sku", target)
            qty = int(payload.get("quantity", 1))
            inv = db.query(SimInventory).filter(SimInventory.sku == sku).first()
            if not inv:
                inv = db.query(SimInventory).filter(SimInventory.sku.ilike(f"%{sku}%")).first()
            if inv:
                inv.reserved_quantity += qty
                execution_details["sku"] = inv.sku
                execution_details["new_reserved_quantity"] = inv.reserved_quantity
                execution_details["message"] = f"Simulated shipment held; reserved {qty} units of SKU {inv.sku} pending inventory restock."

        elif action_type in ("reset_credentials", "provision_access"):
            execution_details["temp_token"] = f"tmp_tok_{uuid.uuid4().hex[:12]}"
            execution_details["message"] = f"Simulated enterprise IAM temporary credentials provisioned for {target}."

        elif action_type in ("dispatch_email", "send_notification"):
            execution_details["message"] = f"Simulated executive resolution dispatch transmitted to {target}."

        else:
            execution_details["message"] = f"Generic simulated action '{action_type}' executed for {target}."

        # Mark action state
        action.status = "executed-simulated"
        action.executed_at = datetime.utcnow()
        action.execution_result_json = json.dumps(execution_details)
        db.commit()

        return execution_details

    @staticmethod
    def rollback_action(db: Session, action: ActionRecord) -> Dict[str, Any]:
        """
        Revert an executed simulated action.
        """
        payload = json.loads(action.payload_json or "{}")
        exec_result = json.loads(action.execution_result_json or "{}")
        action_type = action.type
        target = action.target

        rollback_details = {
            "rolled_back_at": datetime.utcnow().isoformat(),
            "target": target,
            "action_type": action_type,
            "success": True
        }

        if action_type in ("issue_credit", "refund_billing", "sla_credit"):
            amount = float(payload.get("amount", action.financial_impact))
            customer_id = payload.get("customer_id", target)
            cust = db.query(SimCustomer).filter(SimCustomer.customer_id == customer_id).first()
            if not cust:
                cust = db.query(SimCustomer).filter(SimCustomer.customer_id.ilike(f"%{customer_id}%")).first()
            if cust:
                cust.credit_balance = max(0.0, cust.credit_balance - amount)
                rollback_details["restored_credit_balance"] = cust.credit_balance

            # Mark credit record reversed
            credit_id = exec_result.get("credit_id")
            if credit_id:
                credit = db.query(SimBillingCredit).filter(SimBillingCredit.credit_id == credit_id).first()
                if credit:
                    credit.status = "reversed"

            rollback_details["message"] = f"Rolled back credit of ${amount:.2f} for {customer_id}."

        elif action_type in ("restart_node", "restart_worker_node"):
            node = db.query(SimNode).filter(SimNode.node_id == target).first()
            if not node:
                node = db.query(SimNode).filter(SimNode.node_id.ilike(f"%{target}%")).first()
            if node:
                node.status = "degraded"
                node.cpu_pct = 95.0
                node.memory_pct = 90.0
                node.last_error = "SIMULATED_REVERT: Restored degraded telemetry post-rollback test"
                rollback_details["message"] = f"Node {node.node_id} state rolled back to previous telemetry snapshot."

        elif action_type in ("hold_shipment", "reserve_inventory"):
            sku = payload.get("sku", target)
            qty = int(payload.get("quantity", 1))
            inv = db.query(SimInventory).filter(SimInventory.sku == sku).first()
            if not inv:
                inv = db.query(SimInventory).filter(SimInventory.sku.ilike(f"%{sku}%")).first()
            if inv:
                inv.reserved_quantity = max(0, inv.reserved_quantity - qty)
                rollback_details["message"] = f"Unreserved {qty} units of SKU {inv.sku}."

        action.status = "rolled-back"
        db.commit()
        return rollback_details
