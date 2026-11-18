from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Department(str, Enum):
    IT = "IT"
    FINANCE = "FINANCE"
    CRM = "CRM"
    INVENTORY = "INVENTORY"
    SECURITY = "SECURITY"
    HR = "HR"

class SLAPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ActionRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ActionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED_SIMULATED = "executed-simulated"
    ROLLED_BACK = "rolled-back"

class ExtractedEntities(BaseModel):
    customer_ids: List[str] = Field(default_factory=list, description="Extracted customer IDs like CUST-10482 or ORG-ACME")
    order_ids: List[str] = Field(default_factory=list, description="Extracted order identifiers like ORD-84729")
    financial_amounts: List[float] = Field(default_factory=list, description="Extracted dollar amounts")
    server_nodes: List[str] = Field(default_factory=list, description="Extracted server/node hosts like node-eu-prod-04")
    error_codes: List[str] = Field(default_factory=list, description="Error codes like ERR_CLUSTER_DOWN or 503")
    timestamps: List[str] = Field(default_factory=list, description="Extracted event timestamps")
    skus: List[str] = Field(default_factory=list, description="Extracted inventory SKUs")
    raw_tags: Dict[str, Any] = Field(default_factory=dict, description="Additional detected attributes")

class DepartmentRouting(BaseModel):
    departments: List[Department] = Field(default_factory=list)
    primary_department: Department = Field(default=Department.IT)
    routing_reason: str = Field(default="")

class TriageResult(BaseModel):
    intent: str = Field(..., description="High-level category of incoming request")
    executive_summary: str = Field(..., description="Concise multi-department summary for operators")
    sla_priority: SLAPriority = Field(default=SLAPriority.MEDIUM)
    routing: DepartmentRouting = Field(default_factory=DepartmentRouting)
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    prompt_injection_detected: bool = Field(default=False)
    security_warning: Optional[str] = None
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    agent_reasoning: str = Field(default="")

class EnrichedContext(BaseModel):
    crm: Dict[str, Any] = Field(default_factory=dict, description="Customer tier, LTV, SLA terms, churn risk")
    infra: Dict[str, Any] = Field(default_factory=dict, description="Server cluster telemetry, node state, CPU/RAM, error logs")
    inventory: Dict[str, Any] = Field(default_factory=dict, description="Stock levels, reservations, backorder policy")
    policy: Dict[str, Any] = Field(default_factory=dict, description="Applicable company guidelines, approval limits")
    retry_count: int = Field(default=0, description="Number of retry attempts required to fetch context")
    degraded_services: List[str] = Field(default_factory=list, description="Microservices that failed and fell back gracefully")
    confidence_score: float = Field(default=0.92, ge=0.0, le=1.0)
    agent_reasoning: str = Field(default="")

class ActionProposed(BaseModel):
    id: str = Field(..., description="Unique action identifier")
    department: Department = Field(..., description="Department responsible for execution")
    type: str = Field(..., description="Action classification: restart_node, issue_credit, hold_shipment, etc.")
    target: str = Field(..., description="Resource target: node name, customer ID, order ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    rationale: str = Field(..., description="Detailed business reasoning")
    financial_impact: float = Field(default=0.0, description="Financial amount involved or protected ($)")
    risk_level: ActionRiskLevel = Field(default=ActionRiskLevel.LOW)
    reversibility: bool = Field(default=True)
    rollback_action: Optional[str] = Field(default=None, description="Corresponding rollback type")
    status: ActionStatus = Field(default=ActionStatus.PENDING)
    requires_approval: bool = Field(default=True, description="True if blocked by hard guardrails")
    guardrail_trigger: Optional[str] = Field(default=None, description="Guardrail rule triggered if applicable")
    manager_comment: Optional[str] = None
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None

class ResolutionPlan(BaseModel):
    actions: List[ActionProposed] = Field(default_factory=list)
    overall_risk: ActionRiskLevel = Field(default=ActionRiskLevel.LOW)
    auto_approvable_count: int = Field(default=0)
    requires_approval_count: int = Field(default=0)
    agent_reasoning: str = Field(default="")

class ReasoningStep(BaseModel):
    step_id: str
    agent_name: str
    title: str
    status: str = "completed"  # pending, in_progress, completed, failed
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    confidence: float = 1.0
    details: Dict[str, Any] = Field(default_factory=dict)

class IncidentCreate(BaseModel):
    title: str
    raw_event: str
    channel: str = "email"  # email, slack, webhook, ticket
    scenario_id: Optional[str] = None

class Incident(BaseModel):
    id: str
    title: str
    raw_event: str
    channel: str
    status: str = "open"  # open, triaged, resolving, resolved, closed
    created_at: datetime
    updated_at: datetime
    triage: Optional[TriageResult] = None
    context: Optional[EnrichedContext] = None
    actions: List[ActionProposed] = Field(default_factory=list)
    reasoning_timeline: List[ReasoningStep] = Field(default_factory=list)
    sla_priority: SLAPriority = SLAPriority.MEDIUM
    financial_impact: float = 0.0

class ApprovalRequest(BaseModel):
    comment: Optional[str] = None

class AuditLogEntry(BaseModel):
    id: str
    incident_id: str
    action_id: Optional[str] = None
    agent: str
    event_type: str  # TRIAGE, ENRICH, ACTION_PROPOSED, APPROVED, REJECTED, EXECUTED, ROLLBACK
    details: Dict[str, Any]
    checksum: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ROIMetrics(BaseModel):
    tickets_resolved: int = 0
    hours_saved: float = 0.0
    dollars_protected: float = 0.0
    mean_time_to_resolution_sec: float = 0.0
    active_incidents: int = 0
    high_stakes_interventions: int = 0
