"""
Cloud-Native Policy Rule Impact Simulation & Audit Governance System
=====================================================================
Enterprise Streamlit UI — dark, structured, decision-support interface.
"""

import streamlit as st
import pandas as pd
from pipeline import run_pipeline
from audit import read_audit_log
from scenario import compare_scenarios, build_comparison_table, get_best_scenario
from visualize import (
    plot_premium_change_heatmap, plot_segment_impact, plot_compliance_violations,
    plot_scenario_comparison_chart, plot_age_distribution_violin
)
from auth import initialize_default_admin, verify_credentials
from agent_api import call_agent, get_audit_history

# ── Initialize authentication ─────────────────────────────────────────────────
initialize_default_admin()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Policy Governance System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] > .main {
    background-color: #0f172a !important;
}
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { background-color: #0f172a !important; }
.block-container { padding: 2rem 3rem 4rem !important; max-width: 1400px !important; }

/* ── Typography ── */
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; }

/* ── Cards ── */
.gov-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.gov-card-accent {
    background: #1e293b;
    border: 1px solid #3b82f6;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}

/* ── Step headers ── */
.step-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}
.step-badge {
    background: #1d4ed8;
    color: #bfdbfe;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.step-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.01em;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #94a3b8 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div > div {
    background: #3b82f6 !important;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 2rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3) !important;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Info / success / error boxes ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
[data-testid="stDataFrame"] thead { background: #0f172a !important; }
.stDataFrame th {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #64748b !important;
    background: #0f172a !important;
}
.stDataFrame td {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
    color: #cbd5e1 !important;
}

/* ── Dividers ── */
hr { border-color: #1e293b !important; margin: 2rem 0 !important; }

/* ── Decision box ── */
.decision-approve {
    background: linear-gradient(135deg, #052e16, #14532d);
    border: 2px solid #22c55e;
    border-radius: 16px;
    padding: 2.5rem;
    text-align: center;
    box-shadow: 0 0 40px rgba(34, 197, 94, 0.15);
}
.decision-reject {
    background: linear-gradient(135deg, #1c0a0a, #450a0a);
    border: 2px solid #ef4444;
    border-radius: 16px;
    padding: 2.5rem;
    text-align: center;
    box-shadow: 0 0 40px rgba(239, 68, 68, 0.15);
}
.decision-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.decision-verdict {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 1rem;
}
.decision-approve .decision-label  { color: #4ade80; }
.decision-approve .decision-verdict { color: #22c55e; }
.decision-reject .decision-label   { color: #f87171; }
.decision-reject .decision-verdict { color: #ef4444; }
.decision-reason {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    font-weight: 400;
    color: #94a3b8;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ── Segment table ── */
.seg-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
}
.seg-table th {
    background: #0f172a;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.68rem;
    padding: 0.6rem 1rem;
    text-align: right;
    border-bottom: 1px solid #334155;
}
.seg-table th:first-child { text-align: left; }
.seg-table td {
    padding: 0.75rem 1rem;
    color: #cbd5e1;
    text-align: right;
    border-bottom: 1px solid #1e293b;
}
.seg-table td:first-child {
    text-align: left;
    font-weight: 500;
    color: #f1f5f9;
}
.seg-table tr:last-child td { border-bottom: none; }
.seg-table tr:hover td { background: rgba(59,130,246,0.04); }

.badge-low    { background:#052e16; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:0.72rem; }
.badge-medium { background:#1c1917; color:#fbbf24; padding:2px 8px; border-radius:4px; font-size:0.72rem; }
.badge-high   { background:#1c0a0a; color:#f87171; padding:2px 8px; border-radius:4px; font-size:0.72rem; }

/* ── Rule preview ── */
.rule-preview {
    background: #0f172a;
    border: 1px solid #1d4ed8;
    border-left: 3px solid #3b82f6;
    border-radius: 6px;
    padding: 0.85rem 1.1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.88rem;
    color: #93c5fd;
}

/* ── Triggered rule badge ── */
.triggered-badge {
    display: inline-block;
    background: #1c0a0a;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    letter-spacing: 0.06em;
    margin-top: 0.5rem;
}

/* ── Audit table ── */
.audit-ts { color: #64748b; font-size: 0.78rem; }
.audit-approve { color: #22c55e; font-weight: 600; }
.audit-reject  { color: #ef4444; font-weight: 600; }

/* ── Flow indicator ── */
.flow-bar {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}
.flow-node {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.25rem 0.65rem;
    border: 1px solid #334155;
    border-radius: 4px;
}
.flow-node.active { color: #93c5fd; border-color: #1d4ed8; background: rgba(29,78,216,0.1); }
.flow-arrow { color: #334155; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def step_header(num: str, title: str):
    st.markdown(
        f'<div class="step-header">'
        f'<span class="step-badge">Step {num}</span>'
        f'<span class="step-title">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def fmt_dollar(v: float) -> str:
    sign = "+" if v > 0 else ""
    return f"{sign}${v:,.2f}"


def fmt_pct(v: float) -> str:
    return f"{v:.2f}%"


def violation_rate_badge(rate: float) -> str:
    if rate == 0:
        return '<span class="badge-low">0%</span>'
    elif rate < 10:
        return f'<span class="badge-medium">{rate:.1f}%</span>'
    else:
        return f'<span class="badge-high">{rate:.1f}%</span>'


# ── Authentication Check ──────────────────────────────────────────────────────
def show_login_page():
    """Display login interface."""
    col_center = st.columns([1, 2, 1])[1]
    
    with col_center:
        st.markdown("""
        <div style="text-align:center; padding: 3rem 0;">
            <div style="font-family:'DM Mono',monospace; font-size:0.72rem; color:#475569;
                        letter-spacing:0.18em; text-transform:uppercase; margin-bottom:0.75rem;">
                🛡️ &nbsp; Cloud-Native Platform
            </div>
            <h1 style="font-family:'Syne',sans-serif; font-size:2.1rem; font-weight:800;
                       color:#f1f5f9; letter-spacing:-0.03em; margin:0; line-height:1.15;">
                Admin Portal
            </h1>
            <p style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#64748b;
                      margin-top:0.75rem; font-weight:300;">
                Policy Rule Impact Simulation &amp; Governance System
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown(
                '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
                'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
                'margin-bottom:0.75rem;">Admin Credentials</div>',
                unsafe_allow_html=True,
            )
            
            username = st.text_input(
                "Username",
                placeholder="admin",
                label_visibility="collapsed"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••",
                label_visibility="collapsed"
            )
            
            submitted = st.form_submit_button("🔓 Login", width='stretch')
            
            if submitted:
                if verify_credentials(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Try again.")
        
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'color:#475569; text-align:center; padding-top:2rem; border-top:1px solid #1e293b;">'
            '<strong>Demo credentials:</strong><br/>'
            'Username: <code style="color:#93c5fd;">admin</code><br/>'
            'Password: <code style="color:#93c5fd;">admin</code>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── Check authentication ──────────────────────────────────────────────────────
if not st.session_state.get("authenticated", False):
    show_login_page()
    st.stop()


# ── Header ────────────────────────────────────────────────────────────────────
# Admin navigation bar
username = st.session_state.get("username", "Unknown")
col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])

with col_nav1:
    st.markdown(
        '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
        'color:#64748b; text-transform:uppercase; letter-spacing:0.1em;">'
        f'👤 &nbsp; Logged in as: <span style="color:#93c5fd;">{username}</span>'
        '</div>',
        unsafe_allow_html=True,
    )

with col_nav3:
    if st.button("🔒 Logout", width='stretch'):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.rerun()

st.divider()

st.markdown("""
<div style="text-align:center; padding: 2.5rem 0 1.5rem;">
    <div style="font-family:'DM Mono',monospace; font-size:0.72rem; color:#475569;
                letter-spacing:0.18em; text-transform:uppercase; margin-bottom:0.75rem;">
        🛡️ &nbsp; Cloud-Native Platform
    </div>
    <h1 style="font-family:'Syne',sans-serif; font-size:2.1rem; font-weight:800;
               color:#f1f5f9; letter-spacing:-0.03em; margin:0; line-height:1.15;">
        Policy Rule Impact Simulation<br>
        <span style="color:#3b82f6;">&amp; Governance System</span>
    </h1>
    <p style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#64748b;
              margin-top:0.75rem; font-weight:300;">
        Simulate, validate, and govern insurance rule changes before deployment
    </p>
</div>
""", unsafe_allow_html=True)

# ── Mode Selector (Manual vs Agent) ───────────────────────────────────────────
mode = st.radio(
    "Select Mode",
    options=["Manual", "Agent"],
    horizontal=True,
    label_visibility="collapsed",
    key="ui_mode"
)

if mode == "Agent":
    st.divider()
    # ══════════════════════════════════════════════════════════════════════════
    # AGENT MODE — Autonomous Rule Evaluation
    # ══════════════════════════════════════════════════════════════════════════
    with st.container():
        st.markdown(
            '<div style="text-align:center; padding:1.5rem 0;">' 
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; color:#64748b; '
            'text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">🤖 Agent Mode</div>'
            '<h2 style="font-family:\'Syne\',sans-serif; font-size:1.5rem; font-weight:700; '
            'color:#f1f5f9; margin:0;">Autonomous Rule Evaluation</h2>'
            '<p style="font-family:\'DM Sans\',sans-serif; font-size:0.88rem; color:#94a3b8; '
            'margin-top:0.5rem;">The agent will evaluate your rule against compliance constraints'
            ' and automatically approve or reject.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            agent_threshold = st.number_input("Age Threshold", min_value=18, max_value=80, value=25, step=1)
        with col2:
            agent_multiplier = st.number_input("Risk Multiplier", min_value=1.0, max_value=3.0, value=1.85, step=0.01)
        with col3:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            run_agent = st.button("🚀 Run Agent", width='stretch')
        
        if run_agent:
            with st.spinner("⏳ Agent evaluating rule..."):
                result = call_agent(
                    task="full_pipeline",
                    threshold=agent_threshold,
                    multiplier=agent_multiplier
                )
            
            if result.get("status") == "success":
                st.session_state["agent_result"] = result
            else:
                st.error(f"❌ Agent Error: {result.get('error', 'Unknown error')}")
        
        # Display agent result if available
        if "agent_result" in st.session_state:
            agent_result = st.session_state["agent_result"]
            st.divider()
            
            col_decision, col_metrics = st.columns([1, 2])
            
            with col_decision:
                decision = agent_result.get("decision", "UNKNOWN")
                reason = agent_result.get("reason", "No reason provided")
                
                if decision == "APPROVE":
                    st.markdown(
                        f'<div class="decision-approve">'
                        f'<div class="decision-label">Agent Decision</div>'
                        f'<div class="decision-verdict">✓ APPROVE</div>'
                        f'<div class="decision-reason">{reason}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="decision-reject">'
                        f'<div class="decision-label">Agent Decision</div>'
                        f'<div class="decision-verdict">✗ REJECT</div>'
                        f'<div class="decision-reason">{reason}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            
            with col_metrics:
                # Extract metrics from analysis and compliance
                analysis = agent_result.get("analysis", {})
                compliance = agent_result.get("compliance", {})
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Policies Affected", analysis.get("affected_policies", "N/A"))
                with col_m2:
                    avg_change = analysis.get("avg_change", 0)
                    st.metric("Avg Premium Δ", f"${avg_change:+.2f}")
                with col_m3:
                    total_impact = analysis.get("total_portfolio_delta", 0)
                    st.metric("Total Impact", f"${total_impact:+.2f}")
            
            # Add automatic Qwen explanation
            st.divider()
            try:
                from ollama_client import check_ollama_running
                from decision_explainer import explain_decision
                
                if check_ollama_running():
                    with st.spinner("🤔 Qwen is explaining the decision..."):
                        explanation = explain_decision(agent_result)
                        st.info(f"💡 **Why this decision?**\n\n{explanation}")
            except Exception as e:
                pass  # Silently fail if Ollama not available
        
        # Show audit history
        st.divider()
        st.subheader("Recent Agent Decisions")
        audit_df = get_audit_history(limit=10)
        if not audit_df.empty:
            st.dataframe(audit_df, width='stretch')
        else:
            st.info("No agent decisions logged yet.")
        
        # ========== INTERACTIVE CHAT WITH QWEN ==========
        if "agent_result" in st.session_state:
            st.divider()
            st.subheader("💬 Ask Qwen About This Decision")
            
            # Initialize chat history in session state
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            
            # Chat input
            user_query = st.chat_input(
                "Ask about the decision, dataset, or metrics...",
                key="agent_chat_input"
            )
            
            if user_query:
                agent_result = st.session_state["agent_result"]
                
                # Add user message to history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_query
                })
                
                with st.chat_message("user"):
                    st.write(user_query)
                
                # Determine query type and route appropriately
                query_lower = user_query.lower()
                
                try:
                    from ollama_client import check_ollama_running
                    
                    if not check_ollama_running():
                        st.error("❌ Ollama not running. Start with: `ollama serve` in another terminal")
                    else:
                        with st.spinner("🤔 Qwen is thinking..."):
                            # Check if it's about decision or dataset
                            if any(word in query_lower for word in 
                                   ["decision", "why", "approved", "rejected", "deployed", "rule", "constraint", "affect", "impact", "change", "premium"]):
                                # Decision-related query
                                from decision_explainer import answer_decision_query
                                response = answer_decision_query(user_query, agent_result)
                            else:
                                # Dataset-related query
                                from query_handler import DatasetQueryHandler
                                from pipeline import _get_dataset
                                
                                df = _get_dataset()
                                handler = DatasetQueryHandler(df)
                                response = handler.answer_dataset_query(user_query)
                        
                        # Add response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                        
                        with st.chat_message("assistant"):
                            st.write(response)
                
                except ConnectionError as e:
                    st.error(f"❌ {str(e)}")
                    st.info("💡 Start Ollama with: `ollama serve` in another terminal")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Make sure Qwen 7B is pulled: `ollama pull qwen:7b`")
        # ========== END CHAT SECTION ==========
    
    st.stop()  # Exit here for Agent mode

st.divider()

# ── Pipeline flow indicator ───────────────────────────────────────────────────
result = st.session_state.get("pipeline_result")
has_result = result is not None

nodes = ["Rule", "Simulation", "Impact", "Compliance", "Decision", "Audit"]
active_idx = 5 if has_result else 0

flow_html = '<div class="flow-bar">'
for i, node in enumerate(nodes):
    cls = "flow-node active" if i <= active_idx and has_result else "flow-node"
    if i == 0: cls = "flow-node active"
    flow_html += f'<span class="{cls}">{node}</span>'
    if i < len(nodes) - 1:
        flow_html += '<span class="flow-arrow">›</span>'
flow_html += "</div>"
st.markdown(flow_html, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — RULE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("1", "Configure Policy Rule")

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        threshold = st.slider(
            "Age Threshold",
            min_value=18, max_value=80, value=25, step=1,
            help="Policies where customer_age is below this value will be flagged for the multiplier.",
        )
        multiplier = st.slider(
            "Risk Multiplier",
            min_value=1.0, max_value=3.0, value=1.85, step=0.01,
            help="The pricing multiplier applied to base_rate for flagged policies.",
        )

    with col_right:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div class="rule-preview">'
            f'<span style="color:#64748b">IF</span> &nbsp;'
            f'customer_age &lt; <strong style="color:#f1f5f9">{threshold}</strong>'
            f'<br/>'
            f'<span style="color:#64748b">THEN</span> &nbsp;'
            f'apply multiplier <strong style="color:#f1f5f9">{multiplier:.2f}</strong>'
            f'<br/><br/>'
            f'<span style="color:#64748b">ELSE</span> &nbsp;'
            f'apply default multiplier <strong style="color:#f1f5f9">1.20</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-family:\'DM Mono\',monospace; font-size:0.72rem; '
            'color:#475569; margin-top:0.5rem;">'
            f'new_premium = base_rate × risk_multiplier'
            '</p>',
            unsafe_allow_html=True,
        )
        # ── FEATURE 1: Rule ID — updates live with every slider change ────────
        rule_id = f"R-{threshold}-{multiplier:.2f}"
        st.markdown(
            f'<div style="'
            f'font-family:\'DM Mono\',monospace;'
            f'font-size:0.75rem;'
            f'color:#64748b;'
            f'margin-top:0.6rem;">'
            f'Rule ID: <span style="color:#93c5fd;">{rule_id}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — RUN SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("2", "Execute Simulation")

    col_btn, col_info = st.columns([1, 3], gap="large")

    with col_btn:
        run_clicked = st.button("▶  Run Simulation", width='stretch')

    with col_info:
        if not has_result:
            st.markdown(
                '<p style="font-family:\'DM Sans\',sans-serif; font-size:0.88rem; '
                'color:#475569; margin-top:0.5rem;">'
                'Configure the rule above, then click Run Simulation to evaluate '
                'portfolio-wide impact across 5,000 policies.'
                '</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="font-family:\'DM Mono\',monospace; font-size:0.8rem; '
                'color:#4ade80;">✓ &nbsp;Simulation complete — results loaded below.</p>',
                unsafe_allow_html=True,
            )

    if run_clicked:
        with st.spinner("Running pipeline…"):
            try:
                st.session_state["pipeline_result"] = run_pipeline(threshold, multiplier)
                st.session_state["rule_config"] = {
                    "threshold": threshold, "multiplier": multiplier
                }
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline error: {e}")

st.divider()

# ── Guard: only render steps 3–7 if simulation has been run ──────────────────
if not has_result:
    st.markdown(
        '<div style="text-align:center; padding:3rem; color:#334155; '
        'font-family:\'DM Mono\',monospace; font-size:0.85rem;">'
        'Steps 3–7 will appear after running the simulation.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Unpack results ────────────────────────────────────────────────────────────
analysis   = result["analysis"]
compliance = result["compliance"]
decision   = result["decision"]
rule_cfg   = st.session_state.get("rule_config", {})

seg        = analysis["segment_analysis"]
comp_seg   = compliance["violations_by_segment"]

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — PORTFOLIO IMPACT
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("3", "Portfolio Impact Analysis")

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.metric("Total Policies", f"{analysis['total_policies']:,}")
    with c2:
        st.metric("Affected Policies", f"{analysis['affected_policies']:,}")
    with c3:
        st.metric("% Affected", fmt_pct(analysis['pct_affected']))
    with c4:
        avg = analysis['avg_change']
        st.metric(
            "Avg Premium Change",
            fmt_dollar(avg),
            delta=f"{'▲' if avg > 0 else '▼'} vs current book",
            delta_color="inverse",
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    delta_val = analysis["total_portfolio_delta"]
    delta_color = "#ef4444" if delta_val < 0 else "#22c55e"
    delta_label = "Net portfolio impact — total change in written premium"
    st.markdown(
        f'<div class="gov-card" style="text-align:center;">'
        f'<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
        f'color:#64748b; text-transform:uppercase; letter-spacing:0.1em; '
        f'margin-bottom:0.4rem;">{delta_label}</div>'
        f'<div style="font-family:\'Syne\',sans-serif; font-size:2.4rem; '
        f'font-weight:800; color:{delta_color}; letter-spacing:-0.02em;">'
        f'{fmt_dollar(delta_val)}'
        f'</div>'
        # ── FEATURE 2: Impact interpretation ─────────────────────────────────
        + (lambda d, avg_cur, total: (
            f'<div style="'
            f'font-family:\'DM Sans\',sans-serif;'
            f'font-size:0.9rem;'
            f'color:#94a3b8;'
            f'margin-top:0.6rem;'
            f'text-align:center;">'
            + (
                f'↑ Portfolio revenue increases by '
                f'{abs(d / (avg_cur * total) * 100):.1f}%'
                if d > 0 else
                f'↓ Portfolio revenue decreases by '
                f'{abs(d / (avg_cur * total) * 100):.1f}%'
            )
            + f'</div>'
        ))(
            delta_val,
            analysis["avg_current_premium"],
            analysis["total_policies"],
        )
        + f'</div>',
        unsafe_allow_html=True,
    )

    # ── FEATURE 3: Color legend ───────────────────────────────────────────────
    st.markdown(
        '<div style="'
        'font-family:\'DM Mono\',monospace;'
        'font-size:0.7rem;'
        'color:#475569;'
        'margin-top:0.8rem;'
        'text-align:center;">'
        '<span style="color:#22c55e;">Green</span> = revenue increase'
        ' &nbsp;&nbsp;|&nbsp;&nbsp; '
        '<span style="color:#ef4444;">Red</span> = revenue decrease'
        '</div>',
        unsafe_allow_html=True,
    )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — SEGMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("4", "Segment-Level Impact")

    seg_labels = ["<25", "25-40", ">40"]
    seg_display = ["Under 25", "Ages 25–40", "Over 40"]

    cols = st.columns(3, gap="medium")

    for col, label, display in zip(cols, seg_labels, seg_display):
        s = seg.get(label, {})
        avg_chg     = s.get("avg_premium_change", 0)
        pct_aff     = s.get("pct_affected", 0)
        count       = s.get("count", 0)
        avg_new     = s.get("avg_new_premium", 0)
        avg_cur     = s.get("avg_current_premium", 0)
        chg_color   = "#ef4444" if avg_chg < 0 else "#22c55e"

        with col:
            st.markdown(
                f'<div class="gov-card">'
                f'<div style="font-family:\'Syne\',sans-serif; font-size:0.95rem; '
                f'font-weight:700; color:#f1f5f9; margin-bottom:0.1rem;">{display}</div>'
                f'<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
                f'color:#64748b; margin-bottom:1rem;">{count:,} policies</div>'
                f'<div style="display:flex; flex-direction:column; gap:0.6rem;">'
                f'<div style="display:flex; justify-content:space-between; '
                f'font-family:\'DM Mono\',monospace; font-size:0.78rem;">'
                f'<span style="color:#64748b">Avg change</span>'
                f'<span style="color:{chg_color}; font-weight:500;">{fmt_dollar(avg_chg)}</span>'
                f'</div>'
                f'<div style="display:flex; justify-content:space-between; '
                f'font-family:\'DM Mono\',monospace; font-size:0.78rem;">'
                f'<span style="color:#64748b">Avg current</span>'
                f'<span style="color:#cbd5e1">${avg_cur:,.2f}</span>'
                f'</div>'
                f'<div style="display:flex; justify-content:space-between; '
                f'font-family:\'DM Mono\',monospace; font-size:0.78rem;">'
                f'<span style="color:#64748b">Avg new</span>'
                f'<span style="color:#93c5fd">${avg_new:,.2f}</span>'
                f'</div>'
                f'<div style="display:flex; justify-content:space-between; '
                f'font-family:\'DM Mono\',monospace; font-size:0.78rem;">'
                f'<span style="color:#64748b">% Affected</span>'
                f'<span style="color:#e2e8f0">{pct_aff:.1f}%</span>'
                f'</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — COMPLIANCE CHECK
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("5", "Regulatory Compliance Check")

    # ── Display compliance rules ────────────────────────────────────────────────
    br = compliance["violations_by_rule"]
    st.markdown(
        f'<div class="gov-card" style="background: #1e2d4d; border-color: #3b82f6;">'
        f'<div style="font-family:\'DM Mono\',monospace; font-size:0.65rem; '
        f'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
        f'margin-bottom:0.8rem;">Compliance Rules</div>'
        f'<div style="display:flex; flex-direction:column; gap:0.8rem;">'
        f'<div style="padding:0.6rem; background:#0f172a; border-left:3px solid #3b82f6; border-radius:4px;">'
        f'<div style="font-family:\'Syne\',sans-serif; font-size:0.85rem; font-weight:600; '
        f'color:#60a5fa; margin-bottom:0.2rem;">Rule 1: Absolute Increase Cap</div>'
        f'<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; color:#cbd5e1;">'
        f'Premium increase <strong style="color:#fbbf24">{br.get("absolute_threshold", "N/A")}</strong> per policy'
        f'</div>'
        f'</div>'
        f'<div style="padding:0.6rem; background:#0f172a; border-left:3px solid #3b82f6; border-radius:4px;">'
        f'<div style="font-family:\'Syne\',sans-serif; font-size:0.85rem; font-weight:600; '
        f'color:#60a5fa; margin-bottom:0.2rem;">Rule 2: Percentage Increase Cap</div>'
        f'<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; color:#cbd5e1;">'
        f'Premium increase <strong style="color:#fbbf24">{br.get("percentage_threshold", "N/A")}</strong> of current premium'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    v_count = compliance["violations_count"]
    v_pct   = compliance["violation_percentage"]

    col_status, col_breakdown = st.columns([1, 2], gap="large")

    with col_status:
        st.metric("Violations Detected", f"{v_count:,}")
        st.metric("Violation Rate", fmt_pct(v_pct))

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if v_count > 0:
            st.error(
                f"⚠️  {v_count:,} compliance violations detected — "
                "rule may not be deployable."
            )
            br = compliance["violations_by_rule"]
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                f'color:#64748b; margin-top:0.5rem; line-height:1.8;">'
                f'Absolute-only: <strong style="color:#fca5a5">{br["absolute_only"]}</strong><br/>'
                f'Percentage-only: <strong style="color:#fca5a5">{br["percentage_only"]}</strong><br/>'
                f'Both rules: <strong style="color:#fca5a5">{br["both_rules"]}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success("✓ No compliance violations detected.")

    with col_breakdown:
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'color:#64748b; text-transform:uppercase; letter-spacing:0.1em; '
            'margin-bottom:0.75rem;">Violations by Age Segment</div>',
            unsafe_allow_html=True,
        )

        rows_html = ""
        for label in ["<25", "25-40", ">40"]:
            s = comp_seg.get(label, {})
            vc    = s.get("violation_count", 0)
            total = s.get("segment_total", 0)
            rate  = s.get("violation_rate_pct", 0)
            badge = violation_rate_badge(rate)
            rows_html += (
                f"<tr>"
                f"<td>{label}</td>"
                f"<td>{vc:,}</td>"
                f"<td>{total:,}</td>"
                f"<td>{badge}</td>"
                f"</tr>"
            )

        st.markdown(
            f'<div class="gov-card" style="padding:1rem 1.5rem;">'
            f'<table class="seg-table">'
            f'<thead><tr>'
            f'<th>Segment</th><th>Violations</th>'
            f'<th>Total Policies</th><th>Rate</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — GOVERNANCE DECISION
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("6", "Governance Decision")

    d_value   = decision["decision"]
    d_reason  = decision["reason"]
    d_rule    = decision.get("triggered_rule")
    d_ts      = decision.get("evaluated_at", "")

    is_approve = d_value == "APPROVE"
    box_class  = "decision-approve" if is_approve else "decision-reject"
    icon       = "✓" if is_approve else "✗"
    label_txt  = "Rule Approved for Deployment" if is_approve else "Deployment Blocked"

    triggered_html = ""
    if d_rule:
        triggered_html = (
            f'<div style="margin-top:1rem;">'
            f'<span class="triggered-badge">Triggered: {d_rule}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="{box_class}">'
        f'<div class="decision-label">{icon} &nbsp; {label_txt}</div>'
        f'<div class="decision-verdict">{d_value}</div>'
        f'<div class="decision-reason">{d_reason}</div>'
        f'{triggered_html}'
        f'<div style="margin-top:1.25rem; font-family:\'DM Mono\',monospace; '
        f'font-size:0.68rem; color:#475569;">Evaluated at {d_ts}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    rs = decision.get("risk_summary", {})
    th = rs.get("thresholds", {})
    if rs and th:
        def gate_icon(passed: bool) -> str:
            return '<span style="color:#22c55e">PASS</span>' if passed \
                   else '<span style="color:#ef4444">FAIL</span>'

        gates = [
            ("Compliance violations",  f"{rs.get('violations',0):,}",
             "0", gate_icon(rs.get('violations', 0) == 0)),
            ("Avg premium change",     fmt_dollar(rs.get('avg_change', 0)),
             f"≤ ${th.get('max_avg_change',300):,.0f}",
             gate_icon(rs.get('avg_change', 0) <= th.get('max_avg_change', 300))),
            ("Portfolio exposure",     fmt_pct(rs.get('affected_percentage', 0)),
             f"≤ {th.get('max_pct_affected',50):.0f}%",
             gate_icon(rs.get('affected_percentage', 0) <= th.get('max_pct_affected', 50))),
        ]

        gate_rows = "".join(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td style='text-align:right; color:#f1f5f9; font-weight:500;'>{value}</td>"
            f"<td style='text-align:right; color:#64748b;'>{threshold_}</td>"
            f"<td style='text-align:right;'>{status}</td>"
            f"</tr>"
            for name, value, threshold_, status in gates
        )

        st.markdown(
            f'<div class="gov-card" style="margin-top:1rem;">'
            f'<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            f'color:#64748b; text-transform:uppercase; letter-spacing:0.1em; '
            f'margin-bottom:0.75rem;">Governance Gate Scorecard</div>'
            f'<table class="seg-table">'
            f'<thead><tr><th>Gate</th><th>Value</th>'
            f'<th>Threshold</th><th>Status</th></tr></thead>'
            f'<tbody>{gate_rows}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("7", "Audit Trail")

    df_log = read_audit_log()

    if df_log.empty:
        st.markdown(
            '<p style="font-family:\'DM Mono\',monospace; font-size:0.82rem; '
            'color:#475569;">No audit records found.</p>',
            unsafe_allow_html=True,
        )
    else:
        df_display = (
            df_log
            .sort_values("timestamp", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )

        # Build styled HTML table
        header_cols = ["#", "Timestamp", "Threshold", "Multiplier",
                       "Decision", "Violations", "Violation %"]
        header_html = "".join(f"<th>{c}</th>" for c in header_cols)

        rows_html = ""
        for i, row in df_display.iterrows():
            dec = str(row.get("decision", ""))
            dec_html = (
                f'<span class="audit-approve">✓ APPROVED</span>' if dec == "APPROVE"
                else f'<span class="audit-reject">✗ REJECTED</span>'
            )
            ts_raw = str(row.get("timestamp", ""))
            ts_short = ts_raw[:19].replace("T", " ") if len(ts_raw) >= 19 else ts_raw

            rows_html += (
                f"<tr>"
                f"<td style='color:#475569;'>{i+1}</td>"
                f"<td class='audit-ts'>{ts_short}</td>"
                f"<td>{row.get('threshold', '—')}</td>"
                f"<td>{row.get('multiplier', '—')}</td>"
                f"<td>{dec_html}</td>"
                f"<td>{int(row.get('violations', 0)):,}</td>"
                f"<td>{float(row.get('violation_percentage', 0)):.2f}%</td>"
                f"</tr>"
            )

        total_records = len(df_log)
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace; font-size:0.72rem; '
            f'color:#475569; margin-bottom:0.75rem;">'
            f'Showing last 5 of {total_records:,} total audit records — '
            f'sorted by most recent first</div>'
            f'<div class="gov-card" style="padding:1rem 1.5rem;">'
            f'<table class="seg-table">'
            f'<thead><tr>{header_html}</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO COMPARISON — Multi-Rule Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("8", "Scenario Comparison")

    st.markdown(
        '<div style="font-family:\'DM Sans\',sans-serif; font-size:0.95rem; '
        'color:#cbd5e1; margin-bottom:1.5rem;">Compare multiple pricing rules side-by-side '
        'to identify optimal outcomes.</div>',
        unsafe_allow_html=True,
    )

    col_add1, col_add2 = st.columns([3, 1], gap="medium")
    
    with col_add1:
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
            'margin-bottom:0.5rem;">Create Scenarios</div>',
            unsafe_allow_html=True,
        )
        
        num_scenarios = st.slider("Number of scenarios to compare", min_value=2, max_value=6, value=3, key="num_scenarios")
    
    with col_add2:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        run_comparison = st.button("▶️ Run Comparison", key="run_comparison", width="stretch")

    # Input fields for each scenario
    scenarios = []
    scenario_cols = st.columns(num_scenarios, gap="small")
    
    for i, col in enumerate(scenario_cols):
        with col:
            st.markdown(
                f'<div style="font-family:\'Syne\',sans-serif; font-size:0.85rem; '
                f'font-weight:600; color:#60a5fa; margin-bottom:0.6rem;">Scenario {i+1}</div>',
                unsafe_allow_html=True,
            )
            scenario_name = st.text_input(
                f"Name",
                value=["Conservative", "Moderate", "Aggressive", "High Growth", "Balanced", "Premium"][i],
                key=f"scenario_name_{i}",
                label_visibility="collapsed"
            )
            scenario_threshold = st.slider(
                f"Threshold",
                min_value=18, max_value=40, value=[20, 25, 30, 35, 27, 28][i],
                key=f"scenario_threshold_{i}",
                label_visibility="collapsed"
            )
            scenario_multiplier = st.slider(
                f"Multiplier",
                min_value=1.05, max_value=2.0, value=[1.10, 1.20, 1.35, 1.50, 1.25, 1.15][i], step=0.05,
                key=f"scenario_multiplier_{i}",
                label_visibility="collapsed"
            )
            
            scenarios.append({
                "name": scenario_name,
                "threshold": scenario_threshold,
                "multiplier": scenario_multiplier,
                "description": f"Threshold: {scenario_threshold}, Multiplier: {scenario_multiplier:.2f}x"
            })

    if run_comparison:
        st.session_state["comparison_results"] = compare_scenarios(scenarios)

    # Display results if available
    if "comparison_results" in st.session_state:
        results = st.session_state["comparison_results"]
        
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # Comparison table
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
            'margin-bottom:0.75rem;">Scenario Results Comparison</div>',
            unsafe_allow_html=True,
        )
        
        comp_table = build_comparison_table(results)
        st.dataframe(comp_table, width="stretch", hide_index=True)

        # Best scenario recommendation
        best_balanced = get_best_scenario(results, criterion="balanced")
        best_deployable = get_best_scenario(results, criterion="deployable")
        best_revenue = get_best_scenario(results, criterion="revenue")

        col_rec1, col_rec2, col_rec3 = st.columns(3, gap="medium")

        with col_rec1:
            if best_balanced:
                st.markdown(
                    f'<div class="gov-card">'
                    f'<div style="font-family:\'DM Mono\',monospace; font-size:0.65rem; '
                    f'color:#60a5fa; text-transform:uppercase; letter-spacing:0.1em; '
                    f'margin-bottom:0.5rem;">⚖️ Balanced Recommendation</div>'
                    f'<div style="font-family:\'Syne\',sans-serif; font-size:0.95rem; '
                    f'font-weight:600; color:#f1f5f9;">{best_balanced["name"]}</div>'
                    f'<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                    f'color:#cbd5e1; margin-top:0.4rem;">Multiplier: {best_balanced["multiplier"]:.2f}x</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with col_rec2:
            if best_deployable:
                st.markdown(
                    f'<div class="gov-card">'
                    f'<div style="font-family:\'DM Mono\',monospace; font-size:0.65rem; '
                    f'color:#22c55e; text-transform:uppercase; letter-spacing:0.1em; '
                    f'margin-bottom:0.5rem;">✓ Most Deployable</div>'
                    f'<div style="font-family:\'Syne\',sans-serif; font-size:0.95rem; '
                    f'font-weight:600; color:#f1f5f9;">{best_deployable["name"]}</div>'
                    f'<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                    f'color:#cbd5e1; margin-top:0.4rem;">Violations: {best_deployable["key_metrics"]["violations"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with col_rec3:
            if best_revenue:
                revenue = best_revenue["key_metrics"]["total_revenue_impact"]
                revenue_color = "#22c55e" if revenue > 0 else "#ef4444"
                st.markdown(
                    f'<div class="gov-card">'
                    f'<div style="font-family:\'DM Mono\',monospace; font-size:0.65rem; '
                    f'color:#fbbf24; text-transform:uppercase; letter-spacing:0.1em; '
                    f'margin-bottom:0.5rem;">💰 Highest Revenue</div>'
                    f'<div style="font-family:\'Syne\',sans-serif; font-size:0.95rem; '
                    f'font-weight:600; color:#f1f5f9;">{best_revenue["name"]}</div>'
                    f'<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                    f'color:#cbd5e1; margin-top:0.4rem;"><span style="color:{revenue_color}">${revenue:,.0f}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Scenario comparison charts
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        
        chart_col1, chart_col2 = st.columns(2, gap="medium")

        with chart_col1:
            fig_revenue = plot_scenario_comparison_chart(results, metric="total_revenue_impact")
            st.plotly_chart(fig_revenue, width="stretch")

        with chart_col2:
            fig_violations = plot_scenario_comparison_chart(results, metric="violations")
            st.plotly_chart(fig_violations, width="stretch")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# RISK VISUALIZATION & HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("9", "Risk Heatmap & Visualization")

    if has_result and result is not None:
        # Extract the enriched dataframe from pipeline for heatmap
        # Recreate it from raw data since it's not stored in result
        from simulation import simulate
        rule_config = st.session_state.get("rule_config", {"threshold": 25, "multiplier": 1.20})
        df_enriched = simulate(pd.read_csv("data/dataset.csv"), 
                              rule_config["threshold"],
                              rule_config["multiplier"])

        tab_heatmap, tab_segments, tab_compliance, tab_violin = st.tabs(
            ["🔥 Premium Change Heatmap", "📊 Segment Impact", "⚠️ Compliance", "📈 Age Distribution"]
        )

        with tab_heatmap:
            st.markdown(
                '<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                'color:#94a3b8; margin-bottom:1rem;">Heatmap showing customer age groups vs premium change ranges. '
                'Brighter colors indicate higher density of policies.</div>',
                unsafe_allow_html=True,
            )
            fig_heatmap = plot_premium_change_heatmap(df_enriched, title="Premium Change Heatmap")
            st.plotly_chart(fig_heatmap, width="stretch")

        with tab_segments:
            st.markdown(
                '<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                'color:#94a3b8; margin-bottom:1rem;">Revenue impact (total portfolio delta) by age segment. '
                'Green = revenue increase, Red = revenue decrease.</div>',
                unsafe_allow_html=True,
            )
            fig_segment = plot_segment_impact(analysis, title="Revenue Impact by Age Segment")
            st.plotly_chart(fig_segment, width="stretch")

        with tab_compliance:
            st.markdown(
                '<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                'color:#94a3b8; margin-bottom:1rem;">Breakdown of compliance violations by rule type. '
                'Shows which regulatory thresholds are being breached.</div>',
                unsafe_allow_html=True,
            )
            fig_compliance = plot_compliance_violations(compliance, title="Compliance Violations Breakdown")
            st.plotly_chart(fig_compliance, width="stretch")

        with tab_violin:
            st.markdown(
                '<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
                'color:#94a3b8; margin-bottom:1rem;">Distribution of premium changes across the age spectrum. '
                'Shows the spread and median changes by age group.</div>',
                unsafe_allow_html=True,
            )
            fig_violin = plot_age_distribution_violin(df_enriched, title="Premium Change Distribution by Age")
            st.plotly_chart(fig_violin, width="stretch")
    
    else:
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; '
            'color:#475569; padding:1rem; background:#1e293b; border-radius:6px;">'
            'Run a simulation first to view risk heatmaps and visualizations.'
            '</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# DATA EXPLORER — Interactive CSV Viewer
# ═══════════════════════════════════════════════════════════════════════════════
with st.container():
    step_header("10", "Data Explorer")

    # Tabs for dataset selection
    tab_dataset, tab_audit = st.tabs(["📊 Policy Dataset", "📋 Audit Log"])

    with tab_dataset:
        try:
            df_dataset = pd.read_csv("data/dataset.csv")
            
            col_info1, col_info2, col_info3 = st.columns(3, gap="medium")
            with col_info1:
                st.metric("Total Records", f"{len(df_dataset):,}")
            with col_info2:
                st.metric("Columns", len(df_dataset.columns))
            with col_info3:
                st.metric("File Size", f"{df_dataset.memory_usage(deep=True).sum() / 1024:.1f} KB")

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            col_search, col_rows = st.columns([2, 1], gap="medium")
            with col_search:
                search_col = st.selectbox(
                    "Filter by column",
                    options=["All"] + list(df_dataset.columns),
                    key="dataset_search_col",
                    label_visibility="collapsed"
                )
            with col_rows:
                rows_to_show = st.slider(
                    "Rows to display",
                    min_value=5,
                    max_value=min(100, len(df_dataset)),
                    value=20,
                    step=5,
                    key="dataset_rows_slider",
                    label_visibility="collapsed"
                )

            if search_col != "All":
                search_term = st.text_input(
                    f"Search in {search_col}",
                    key="dataset_search_term",
                    placeholder=f"Filter by {search_col}...",
                    label_visibility="collapsed"
                )
                if search_term:
                    df_filtered = df_dataset[
                        df_dataset[search_col].astype(str).str.contains(search_term, case=False, na=False)
                    ]
                else:
                    df_filtered = df_dataset
            else:
                df_filtered = df_dataset

            df_display = df_filtered.head(rows_to_show)

            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace; font-size:0.72rem; '
                f'color:#475569; margin-bottom:0.75rem;">'
                f'Showing {len(df_display):,} of {len(df_filtered):,} records '
                f'(total dataset: {len(df_dataset):,})</div>',
                unsafe_allow_html=True,
            )

            st.dataframe(df_display, width="stretch", hide_index=False)

            # Download button
            csv_data = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered CSV",
                data=csv_data,
                file_name="dataset_filtered.csv",
                mime="text/csv",
                key="download_dataset"
            )

        except FileNotFoundError:
            st.error("❌ dataset.csv not found in data/ directory")

    with tab_audit:
        try:
            df_audit = read_audit_log()
            
            col_info1, col_info2, col_info3 = st.columns(3, gap="medium")
            with col_info1:
                st.metric("Total Records", f"{len(df_audit):,}")
            with col_info2:
                st.metric("Columns", len(df_audit.columns))
            with col_info3:
                st.metric("File Size", f"{df_audit.memory_usage(deep=True).sum() / 1024:.1f} KB")

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            col_search2, col_rows2 = st.columns([2, 1], gap="medium")
            with col_search2:
                search_col_audit = st.selectbox(
                    "Filter by column",
                    options=["All"] + list(df_audit.columns),
                    key="audit_search_col",
                    label_visibility="collapsed"
                )
            with col_rows2:
                rows_to_show_audit = st.slider(
                    "Rows to display",
                    min_value=5,
                    max_value=min(100, len(df_audit)),
                    value=20,
                    step=5,
                    key="audit_rows_slider",
                    label_visibility="collapsed"
                )

            if search_col_audit != "All":
                search_term_audit = st.text_input(
                    f"Search in {search_col_audit}",
                    key="audit_search_term",
                    placeholder=f"Filter by {search_col_audit}...",
                    label_visibility="collapsed"
                )
                if search_term_audit:
                    df_filtered_audit = df_audit[
                        df_audit[search_col_audit].astype(str).str.contains(search_term_audit, case=False, na=False)
                    ]
                else:
                    df_filtered_audit = df_audit
            else:
                df_filtered_audit = df_audit

            df_display_audit = df_filtered_audit.head(rows_to_show_audit)

            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace; font-size:0.72rem; '
                f'color:#475569; margin-bottom:0.75rem;">'
                f'Showing {len(df_display_audit):,} of {len(df_filtered_audit):,} records '
                f'(total audit log: {len(df_audit):,})</div>',
                unsafe_allow_html=True,
            )

            st.dataframe(df_display_audit, width="stretch", hide_index=False)

            # Download button
            csv_data_audit = df_filtered_audit.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered CSV",
                data=csv_data_audit,
                file_name="audit_log_filtered.csv",
                mime="text/csv",
                key="download_audit"
            )

        except FileNotFoundError:
            st.error("❌ Audit log not found")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL — User & System Management
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Admin Settings", expanded=False):
    from auth import get_admin_list, create_admin, delete_admin, change_password
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["👥 Users", "🔐 Change Password", "ℹ️ System"])
    
    with admin_tab1:
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
            'margin-bottom:0.75rem;">Manage Admin Users</div>',
            unsafe_allow_html=True,
        )
        
        col_list, col_create = st.columns([1, 1], gap="medium")
        
        with col_list:
            st.markdown(
                '<div style="font-family:\'Syne\',sans-serif; font-size:0.9rem; '
                'font-weight:600; color:#f1f5f9; margin-bottom:0.5rem;">Active Admins</div>',
                unsafe_allow_html=True,
            )
            admin_list = get_admin_list()
            for admin in admin_list:
                col_name, col_del = st.columns([3, 1], gap="small")
                with col_name:
                    current_user = " (you)" if admin == username else ""
                    st.markdown(
                        f'<div style="font-family:\'DM Mono\',monospace; font-size:0.85rem; '
                        f'color:#cbd5e1;">👤 {admin}{current_user}</div>',
                        unsafe_allow_html=True,
                    )
                with col_del:
                    if admin != username:  # Can't delete yourself
                        if st.button("🗑️", key=f"delete_{admin}", help=f"Delete {admin}"):
                            if delete_admin(admin):
                                st.success(f"Deleted {admin}")
                                st.rerun()
                            else:
                                st.error("Failed to delete user")
        
        with col_create:
            st.markdown(
                '<div style="font-family:\'Syne\',sans-serif; font-size:0.9rem; '
                'font-weight:600; color:#f1f5f9; margin-bottom:0.5rem;">Add New Admin</div>',
                unsafe_allow_html=True,
            )
            new_admin_name = st.text_input("New username", key="new_admin_name", label_visibility="collapsed")
            new_admin_pass = st.text_input("Password", type="password", key="new_admin_pass", label_visibility="collapsed")
            
            if st.button("➕ Create Admin", width="stretch"):
                if not new_admin_name or not new_admin_pass:
                    st.error("Username and password required")
                elif create_admin(new_admin_name, new_admin_pass):
                    st.success(f"✓ Admin '{new_admin_name}' created")
                    st.rerun()
                else:
                    st.error(f"User '{new_admin_name}' already exists")
    
    with admin_tab2:
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
            'margin-bottom:0.75rem;">Change Your Password</div>',
            unsafe_allow_html=True,
        )
        
        with st.form("change_password_form"):
            old_pass = st.text_input("Current password", type="password", label_visibility="collapsed")
            new_pass = st.text_input("New password", type="password", label_visibility="collapsed")
            confirm_pass = st.text_input("Confirm new password", type="password", label_visibility="collapsed")
            
            if st.form_submit_button("🔓 Update Password", width="stretch"):
                if not old_pass or not new_pass or not confirm_pass:
                    st.error("All fields required")
                elif new_pass != confirm_pass:
                    st.error("New passwords don't match")
                elif change_password(username, old_pass, new_pass):
                    st.success("✓ Password updated successfully")
                else:
                    st.error("❌ Current password incorrect")
    
    with admin_tab3:
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; '
            'text-transform:uppercase; letter-spacing:0.1em; color:#94a3b8; '
            'margin-bottom:0.75rem;">System Information</div>',
            unsafe_allow_html=True,
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current User", username)
        with col2:
            st.metric("Total Admins", len(get_admin_list()))
        with col3:
            import os
            audit_exists = os.path.exists("data/audit_log.csv")
            st.metric("Audit Log", "✓ Active" if audit_exists else "⚠️ Missing")
        
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        
        st.info(
            "🔐 **Security Note**: This is a demo interface. For production, use OAuth, LDAP, or enterprise SSO. "
            "Credentials are hashed but stored locally."
        )

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; margin-top:2rem;
            border-top: 1px solid #1e293b;">
    <span style="font-family:'DM Mono',monospace; font-size:0.7rem; color:#334155;">
        Cloud-Native Policy Rule Impact Simulation &amp; Audit Governance System
        &nbsp;·&nbsp; Internal Use Only &nbsp;·&nbsp; All decisions are logged
    </span>
</div>
""", unsafe_allow_html=True)