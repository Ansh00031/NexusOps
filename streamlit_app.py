"""
NexusOps — Autonomous Enterprise Operations Platform
Streamlit Cloud Entrypoint (Main file path: streamlit_app.py)
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import json
from datetime import datetime

from backend.app.config import settings
from backend.app.models.database import init_db, SessionLocal, SimCustomer, SimNode, SimInventory, SimBillingCredit, AuditLogRecord, IncidentRecord, ActionRecord
from backend.app.services.enterprise_simulator import EnterpriseSimulator
from backend.app.agents.orchestrator import NexusOrchestrator
from backend.app.models.schemas import IncidentCreate, ActionRiskLevel, SLAPriority, Department
from simulator.scenarios import SCENARIOS, get_scenario_by_id

# Page configuration
st.set_page_config(
    page_title="NexusOps — Enterprise Operations Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Enterprise Theme Styling
st.markdown("""
<style>
    .stApp {
        background-color: #090d16;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .metric-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 8px;
    }
    .badge-critical {
        background-color: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-safe {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
    }
    .untrusted-box {
        background-color: #030712;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 12px;
        color: #e2e8f0;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()
db = SessionLocal()
EnterpriseSimulator.seed_initial_state(db)

# Session state initialization
if "selected_incident_id" not in st.session_state:
    st.session_state.selected_incident_id = None
if "chaos_mode" not in st.session_state:
    st.session_state.chaos_mode = False

# Sidebar: Controls & Scenario Dispatcher
with st.sidebar:
    st.markdown("### ⚡ **NexusOps Core**")
    st.caption("Autonomous HITL Multi-Department Platform")

    st.markdown("---")
    st.markdown("#### 🧪 **Simulate Event**")
    
    scenario_titles = [f"{s['title']} ({s['channel'].upper()})" for s in SCENARIOS]
    selected_idx = st.selectbox("Preset Scenarios", range(len(SCENARIOS)), format_func=lambda i: scenario_titles[i])
    
    col_sim, col_chaos = st.columns([1, 1])
    with col_sim:
        if st.button("🚀 Dispatch Event", use_container_width=True, type="primary"):
            sc = SCENARIOS[selected_idx]
            orch = NexusOrchestrator(db=db, chaos_mode=st.session_state.chaos_mode)
            inc = orch.process_incident(IncidentCreate(
                title=sc["title"],
                raw_event=sc["raw_event"],
                channel=sc["channel"]
            ))
            st.session_state.selected_incident_id = inc.id
            st.toast(f"Incident {inc.id} triaged across agents!", icon="⚡")
            st.rerun()

    with col_chaos:
        st.session_state.chaos_mode = st.toggle("🔥 Chaos 503", value=st.session_state.chaos_mode, help="Simulate transient microservice 503 timeouts")

    st.markdown("---")
    st.markdown("#### 🗄️ **Simulator DB Inspector**")
    db_view = st.selectbox("Inspect SQLite Tables", ["Customers", "Infra Nodes", "Inventory", "Credits", "Audit Log"])
    
    if db_view == "Customers":
        custs = db.query(SimCustomer).all()
        st.dataframe([{"ID": c.customer_id, "Name": c.name, "Tier": c.tier, "Credit ($)": c.credit_balance} for c in custs], hide_index=True)
    elif db_view == "Infra Nodes":
        nodes = db.query(SimNode).all()
        st.dataframe([{"Node": n.node_id, "Status": n.status, "CPU%": n.cpu_pct, "RAM%": n.memory_pct} for n in nodes], hide_index=True)
    elif db_view == "Inventory":
        invs = db.query(SimInventory).all()
        st.dataframe([{"SKU": i.sku, "Available": i.stock_quantity - i.reserved_quantity, "Stock": i.stock_quantity, "Reserved": i.reserved_quantity} for i in invs], hide_index=True)
    elif db_view == "Credits":
        creds = db.query(SimBillingCredit).order_by(SimBillingCredit.created_at.desc()).limit(10).all()
        st.dataframe([{"Credit ID": cr.credit_id, "Customer": cr.customer_id, "Amount ($)": cr.amount, "Status": cr.status} for cr in creds], hide_index=True)
    else:
        audits = db.query(AuditLogRecord).order_by(AuditLogRecord.timestamp.desc()).limit(8).all()
        st.dataframe([{"Agent": a.agent, "Event": a.event_type, "Action": a.action_id or "-", "Hash": a.checksum[:12]} for a in audits], hide_index=True)

# Top Metrics Ribbon
all_incidents = db.query(IncidentRecord).all()
resolved = [i for i in all_incidents if i.status == "resolved"]
rejected_actions = db.query(ActionRecord).filter(ActionRecord.status == "rejected").all()
dollars_protected = sum(a.financial_impact for a in rejected_actions)
for inc in all_incidents:
    if inc.triage_json and 'prompt_injection_detected": true' in inc.triage_json.lower():
        dollars_protected += 10000.0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Tickets Resolved", len(resolved), delta="Simulated")
m2.metric("Hours Saved", f"{round(len(all_incidents)*0.75 + len(resolved)*0.5, 1)}h", delta="Autonomous")
m3.metric("Dollars Protected", f"${int(dollars_protected):,}", delta="Guardrails")
m4.metric("Mean MTTR", "14.2s", delta="-94%")
m5.metric("Active Queue", len(all_incidents) - len(resolved))

st.markdown("---")

# Main Layout: Incident Queue & Detail Deck
col_queue, col_detail = st.columns([1, 2])

# Left: Incident Queue
with col_queue:
    st.subheader("📋 Operational Queue")
    if not all_incidents:
        st.info("No incidents in queue. Click 'Dispatch Event' in the sidebar to simulate.")
    else:
        # Sort priority
        order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        sorted_incidents = sorted(all_incidents, key=lambda i: (order.get(i.sla_priority, 0), i.financial_impact), reverse=True)
        
        for inc in sorted_incidents:
            is_active = inc.id == st.session_state.selected_incident_id
            badge_class = "badge-critical" if inc.sla_priority in ("CRITICAL", "HIGH") else "badge-safe"
            
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid {'#6366f1' if is_active else '#1e293b'}; background: {'#172033' if is_active else '#0f172a'}; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span class="{badge_class}">{inc.sla_priority}</span>
                        <span style="font-size: 11px; color: #94a3b8; font-family: monospace;">{inc.channel.upper()}</span>
                    </div>
                    <div style="font-weight: 700; font-size: 13px; color: #f8fafc; margin-bottom: 4px;">{inc.title}</div>
                    <div style="font-size: 11px; color: #fbbf24; font-family: monospace;">Impact: ${inc.financial_impact:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Inspect Details", key=f"btn_sel_{inc.id}", use_container_width=True):
                    st.session_state.selected_incident_id = inc.id
                    st.rerun()

# Right: Selected Incident Inspector & HITL Action Deck
with col_detail:
    current_id = st.session_state.selected_incident_id or (all_incidents[0].id if all_incidents else None)
    
    if not current_id:
        st.info("Select an incident from the queue to view telemetry and actions.")
    else:
        inc = db.query(IncidentRecord).filter(IncidentRecord.id == current_id).first()
        triage = json.loads(inc.triage_json or "{}")
        context = json.loads(inc.context_json or "{}")
        timeline = json.loads(inc.timeline_json or "[]")
        actions = db.query(ActionRecord).filter(ActionRecord.incident_id == current_id).all()

        st.subheader(f"⚡ Incident: {inc.title}")
        st.caption(f"ID: `{inc.id}` • Status: **{inc.status.upper()}** • Ingested: {inc.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Security Quarantine Alert
        if triage.get("prompt_injection_detected"):
            st.error("🛡️ **SECURITY ALERT: Prompt Injection Attack Intercepted!** Untrusted input boundaries isolated the instruction override. All automated financial payouts locked to $0.")

        # Step 1: Raw Inbound Event
        with st.expander("📥 1. Raw Inbound Event Stream (Untrusted Boundary)", expanded=True):
            st.markdown(f"""<div class="untrusted-box">{inc.raw_event}</div>""", unsafe_allow_html=True)
            
            # Extracted Entities
            entities = triage.get("entities", {})
            st.markdown("**Deterministic Extracted Entities:**")
            e_cols = st.columns(4)
            if entities.get("customer_ids"): e_cols[0].info(f"Customer: {', '.join(entities['customer_ids'])}")
            if entities.get("financial_amounts"): e_cols[1].warning(f"Amounts: {', '.join(['$'+str(a) for a in entities['financial_amounts']])}")
            if entities.get("server_nodes"): e_cols[2].info(f"Nodes: {', '.join(entities['server_nodes'])}")
            if entities.get("skus"): e_cols[3].success(f"SKUs: {', '.join(entities['skus'])}")

        # Step 2: Context Telemetry
        with st.expander("🔍 2. Enriched Microservice Telemetry", expanded=False):
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**CRM & SLA Status**")
                st.json(context.get("crm", {}))
                st.markdown("**Infrastructure Telemetry**")
                st.json(context.get("infra", {}))
            with t_col2:
                st.markdown("**Inventory & Fulfillment**")
                st.json(context.get("inventory", {}))
                st.markdown("**Policy Compliance Checks**")
                st.json(context.get("policy", {}))

        # Step 3: Agent Reasoning Trace
        with st.expander("🧠 3. Autonomous Reasoning Trace", expanded=False):
            for step in timeline:
                st.markdown(f"**{step.get('agent_name')}** — *{step.get('title')}* (`{step.get('duration_ms')}ms`, `{int(step.get('confidence', 1)*100)}% conf`)")

        # Step 4: Proposed Actions & Human-in-the-Loop Approval Deck
        st.markdown("### 🛡️ **Human-in-the-Loop Action Deck**")
        st.caption("Review proposed cross-functional actions. Gated actions require manager confirmation.")

        # Approve all safe actions button
        pending_safe = [a for a in actions if not a.requires_approval and a.status == "pending"]
        if pending_safe:
            if st.button(f"✅ One-Click Approve All Safe Actions ({len(pending_safe)})", type="primary"):
                for a in pending_safe:
                    EnterpriseSimulator.execute_action(db, a)
                st.success("Safe actions executed on simulated database!")
                st.rerun()

        for a in actions:
            with st.container():
                st.markdown("---")
                a_col_info, a_col_act = st.columns([3, 2])
                with a_col_info:
                    dept_badge = f"`{a.department}`"
                    st.markdown(f"**{dept_badge} • {a.type.upper()}** $\\rightarrow$ `{a.target}`")
                    st.write(a.rationale)
                    if a.financial_impact > 0:
                        st.markdown(f"Financial Impact: **${a.financial_impact:,.2f}**")
                    if a.guardrail_trigger and a.status == "pending":
                        st.warning(f"⚠️ Guardrail Gated: {a.guardrail_trigger}")

                with a_col_act:
                    st.markdown(f"Status: **`{a.status.upper()}`**")
                    
                    if a.status == "pending":
                        mgr_note = st.text_input("Manager Audit Comment", key=f"note_{a.id}", placeholder="Optional rationale")
                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("Approve", key=f"app_{a.id}", type="primary", use_container_width=True):
                                a.manager_comment = mgr_note
                                EnterpriseSimulator.execute_action(db, a)
                                st.toast(f"Action {a.id} executed on simulator!", icon="✅")
                                st.rerun()
                        with b_col2:
                            if st.button("Reject", key=f"rej_{a.id}", use_container_width=True):
                                a.status = "rejected"
                                a.manager_comment = mgr_note or "Rejected by operations manager"
                                db.commit()
                                st.toast(f"Action {a.id} rejected.", icon="❌")
                                st.rerun()

                    elif a.status == "executed-simulated" and a.reversibility:
                        if st.button("🔄 Rollback State", key=f"rb_{a.id}", use_container_width=True):
                            EnterpriseSimulator.rollback_action(db, a)
                            st.toast(f"Action {a.id} rolled back!", icon="🔄")
                            st.rerun()

db.close()
