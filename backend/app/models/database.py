from __future__ import annotations
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

Base = declarative_base()

class IncidentRecord(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    channel = Column(String(64), default="email")
    raw_event = Column(Text, nullable=False)
    status = Column(String(64), default="open")
    sla_priority = Column(String(32), default="MEDIUM")
    financial_impact = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # JSON-encoded payload dumps
    triage_json = Column(Text, nullable=True)
    context_json = Column(Text, nullable=True)
    timeline_json = Column(Text, nullable=True)

class ActionRecord(Base):
    __tablename__ = "actions"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False, index=True)
    department = Column(String(32), nullable=False)
    type = Column(String(64), nullable=False)
    target = Column(String(128), nullable=False)
    payload_json = Column(Text, default="{}")
    rationale = Column(Text, nullable=False)
    financial_impact = Column(Float, default=0.0)
    risk_level = Column(String(32), default="LOW")
    reversibility = Column(Boolean, default=True)
    rollback_action = Column(String(64), nullable=True)
    status = Column(String(32), default="pending")  # pending, approved, rejected, executed-simulated, rolled-back
    requires_approval = Column(Boolean, default=True)
    guardrail_trigger = Column(String(255), nullable=True)
    manager_comment = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_result_json = Column(Text, nullable=True)

class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False, index=True)
    action_id = Column(String(64), nullable=True, index=True)
    agent = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    details_json = Column(Text, nullable=False)
    checksum = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ==========================================
# Stateful Mock Enterprise Simulator Tables
# ==========================================

class SimCustomer(Base):
    __tablename__ = "sim_customers"

    customer_id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    tier = Column(String(32), default="Standard")  # VIP, Enterprise, Pro, Standard
    ltv = Column(Float, default=15000.0)
    credit_balance = Column(Float, default=0.0)
    sla_level = Column(String(64), default="99.9% Uptime SLA")
    churn_risk = Column(String(32), default="Low")
    status = Column(String(32), default="Active")

class SimNode(Base):
    __tablename__ = "sim_nodes"

    node_id = Column(String(64), primary_key=True)
    cluster = Column(String(64), default="prod-eu-west")
    status = Column(String(32), default="healthy")  # healthy, degraded, offline
    cpu_pct = Column(Float, default=34.0)
    memory_pct = Column(Float, default=52.0)
    last_error = Column(String(255), nullable=True)
    last_restarted_at = Column(DateTime, default=datetime.utcnow)

class SimInventory(Base):
    __tablename__ = "sim_inventory"

    sku = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    stock_quantity = Column(Integer, default=100)
    reserved_quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=99.0)
    min_threshold = Column(Integer, default=20)

class SimBillingCredit(Base):
    __tablename__ = "sim_billing_credits"

    credit_id = Column(String(64), primary_key=True)
    customer_id = Column(String(64), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(32), default="applied")  # applied, reversed
    created_at = Column(DateTime, default=datetime.utcnow)

class SimPolicyRule(Base):
    __tablename__ = "sim_policy_rules"

    rule_key = Column(String(64), primary_key=True)
    category = Column(String(64), nullable=False)
    max_auto_approved_amount = Column(Float, default=100.0)
    description = Column(String(255), nullable=False)
    requires_approval_conditions = Column(Text, default="[]")

# Engine & Session setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
