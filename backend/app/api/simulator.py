import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from backend.app.models.database import (
    get_db, SimCustomer, SimNode, SimInventory, SimBillingCredit, AuditLogRecord
)
from backend.app.config import settings
from simulator.scenarios import SCENARIOS

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

from backend.app.services.audit_logger import AuditLogger

@router.get("/audit/verify")
def verify_audit_log(db: Session = Depends(get_db)):
    """Validate the cryptographic SHA-256 hash chain of the immutable audit log."""
    is_valid, error, count = AuditLogger.verify_chain_integrity(db)
    return {
        "tamper_free": is_valid,
        "records_verified": count,
        "error": error,
        "status": "VALID" if is_valid else "TAMPERED"
    }

@router.get("/scenarios")
def list_scenarios():
    return SCENARIOS

@router.get("/chaos")
def get_chaos_status():
    return {"chaos_mode": settings.chaos_mode}

@router.post("/chaos")
def toggle_chaos_mode(enabled: bool = Body(..., embed=True)):
    settings.chaos_mode = enabled
    return {"chaos_mode": settings.chaos_mode, "message": f"Chaos mode set to {enabled}"}

@router.get("/state")
def get_simulator_state(db: Session = Depends(get_db)):
    customers = db.query(SimCustomer).all()
    nodes = db.query(SimNode).all()
    inventory = db.query(SimInventory).all()
    credits = db.query(SimBillingCredit).order_by(SimBillingCredit.created_at.desc()).limit(20).all()
    recent_audit = db.query(AuditLogRecord).order_by(AuditLogRecord.timestamp.desc()).limit(20).all()

    return {
        "customers": [
            {
                "customer_id": c.customer_id,
                "name": c.name,
                "tier": c.tier,
                "credit_balance": c.credit_balance,
                "ltv": c.ltv,
                "status": c.status
            } for c in customers
        ],
        "nodes": [
            {
                "node_id": n.node_id,
                "cluster": n.cluster,
                "status": n.status,
                "cpu_pct": n.cpu_pct,
                "memory_pct": n.memory_pct,
                "last_error": n.last_error
            } for n in nodes
        ],
        "inventory": [
            {
                "sku": i.sku,
                "name": i.name,
                "stock_quantity": i.stock_quantity,
                "reserved_quantity": i.reserved_quantity,
                "available_quantity": i.stock_quantity - i.reserved_quantity,
                "unit_price": i.unit_price
            } for i in inventory
        ],
        "credits": [
            {
                "credit_id": cr.credit_id,
                "customer_id": cr.customer_id,
                "amount": cr.amount,
                "reason": cr.reason,
                "status": cr.status,
                "created_at": cr.created_at.isoformat()
            } for cr in credits
        ],
        "audit_logs": [
            {
                "id": a.id,
                "incident_id": a.incident_id,
                "action_id": a.action_id,
                "agent": a.agent,
                "event_type": a.event_type,
                "details": json.loads(a.details_json or "{}"),
                "checksum": a.checksum,
                "timestamp": a.timestamp.isoformat()
            } for a in recent_audit
        ]
    }
