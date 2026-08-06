from __future__ import annotations

import html
from typing import Any

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8002"
SIMULATION_ENDPOINT = "simulation/sequential"

st.set_page_config(page_title="Batch Fraud Policy Evaluation", page_icon="📦", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1500px;}
.hero {padding: 1.25rem 1.4rem; border: 1px solid rgba(30,136,229,.28); border-radius: 14px;
background: linear-gradient(135deg, rgba(25,118,210,.16), rgba(46,125,50,.08)); margin-bottom: 1rem;}
.hero h1 {margin:0 0 .45rem 0;}
.section-intro {padding: 1rem 1.1rem; margin: .45rem 0 1rem; border-left: 4px solid #1976d2;
border-radius: 10px; background: rgba(25,118,210,.09); line-height:1.55;}
.card {min-height:155px; padding:1rem 1.05rem; border:1px solid rgba(128,128,128,.25);
border-radius:14px; background:rgba(128,128,128,.045);}
.metric-card {min-height:150px; padding:1rem; border:1px solid rgba(128,128,128,.25); border-radius:14px;
background:rgba(128,128,128,.045); border-top:4px solid #1976d2;}
.metric-card .value {font-size:1.75rem; font-weight:700; margin:.45rem 0;}
.takeaway {padding:1rem 1.1rem; border-left:5px solid #2e7d32; border-radius:12px;
background:rgba(46,125,50,.10); line-height:1.55;}
.warning {padding:1rem 1.1rem; border-left:5px solid #ef6c00; border-radius:12px;
background:rgba(239,108,0,.10); line-height:1.55;}
</style>
""", unsafe_allow_html=True)


def n(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def i(value: Any) -> int:
    return int(round(n(value)))


def money(value: Any) -> str:
    return f"€{n(value):,.2f}"


def section_intro(title: str, text: str) -> None:
    st.markdown(f'<div class="section-intro"><strong>{html.escape(title)}</strong><br>{html.escape(text)}</div>', unsafe_allow_html=True)


def metric(title: str, value: str, text: str) -> None:
    st.markdown(f'<div class="metric-card"><strong>{html.escape(title)}</strong><div class="value">{html.escape(value)}</div><span>{html.escape(text)}</span></div>', unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_data(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}/{SIMULATION_ENDPOINT}", params=params, timeout=180)
    response.raise_for_status()
    return response.json()


st.markdown("""
<div class="hero">
<h1>📦 Batch Fraud Policy Evaluation</h1>
<p>Global evaluation of Static and Adaptive alert-selection policies before chronological capacity and suppression constraints are introduced.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("Batch evaluation settings")
transaction_limit = st.sidebar.selectbox("Transactions evaluated", [1000, 3000, 10000, 50000], index=2)
investigation_cost = st.sidebar.number_input("Cost per investigation", min_value=0.0, value=10.0, step=1.0)
static_threshold = st.sidebar.slider("Static fraud threshold", 0.0, 1.0, 0.5, 0.01)
budget_multiplier = st.sidebar.slider("Adaptive alert budget multiplier", 0.0, 2.0, 1.4, 0.1)
risk_zone_floor = st.sidebar.slider("Risk-zone floor", 0.0, 1.0, 0.30, 0.01)
alert_rate_low = st.sidebar.slider("Low alert-rate boundary", 0.0, 1.0, 0.03, 0.01)
alert_rate_high = st.sidebar.slider("High alert-rate boundary", 0.0, 1.0, 0.10, 0.01)
if st.sidebar.button("Refresh results", use_container_width=True):
    st.cache_data.clear()
st.sidebar.caption(f"API: `{API_BASE_URL}`")

# Sequential parameters are supplied only because the shared backend endpoint expects them.
params = {
    "limit": int(transaction_limit),
    "investigation_cost": float(investigation_cost),
    "static_threshold": float(static_threshold),
    "ranking_policy": "risk_zone",
    "risk_zone_floor": float(risk_zone_floor),
    "alert_rate_low": float(alert_rate_low),
    "alert_rate_high": float(alert_rate_high),
    "budget_multiplier": float(budget_multiplier),
    "alert_budget_per_step": 30,
    "suppression_window": 3,
    "monitoring_window_size": 1000,
}

try:
    with st.spinner("Running Batch policy evaluation..."):
        data = load_data(params)
except requests.exceptions.ConnectionError:
    st.error("FastAPI is not available. Run: `py -m uvicorn app.api.main:app --reload --port 8002`")
    st.stop()
except requests.exceptions.RequestException as exc:
    st.error("The API request failed.")
    st.exception(exc)
    st.stop()

static = data.get("static_batch", {}).get("summary", {})
adaptive = data.get("adaptive_batch", {}).get("summary", {})
parameters = data.get("parameters", {})

summary_tab, comparison_tab, cost_tab, interpretation_tab, technical_tab = st.tabs([
    "1. Executive Summary", "2. Policy Comparison", "3. Cost & Workload", "4. Research Interpretation", "5. Technical Details"
])

with summary_tab:
    st.header("Executive Summary")
    section_intro("What does this dashboard answer?", "Which alert-selection policy provides the best balance between fraud detection, investigation workload and total operational cost when the complete evaluation set is considered globally?")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><h3>Static Batch</h3><p>Uses one fixed fraud-score threshold. Every transaction above that threshold becomes an alert.</p><p><strong>Purpose:</strong> transparent baseline.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><h3>Adaptive Batch</h3><p>Uses risk-zone and budget-aware logic to select a broader, operationally useful alert set.</p><p><strong>Purpose:</strong> test whether adaptive decision logic improves policy quality.</p></div>', unsafe_allow_html=True)

    cols = st.columns(4)
    values = [
        ("Adaptive recall", f"{n(adaptive.get('recall')):.1%}", f"{n(adaptive.get('recall'))-n(static.get('recall')):+.1%} vs Static"),
        ("Frauds detected", f"{i(adaptive.get('frauds_detected')):,}", f"{i(adaptive.get('frauds_detected'))-i(static.get('frauds_detected')):+,} vs Static"),
        ("Adaptive alerts", f"{i(adaptive.get('selected_alerts')):,}", f"{i(adaptive.get('selected_alerts'))-i(static.get('selected_alerts')):+,} vs Static"),
        ("Adaptive cost", money(adaptive.get('total_operational_cost')), f"{money(n(adaptive.get('total_operational_cost'))-n(static.get('total_operational_cost')))} difference"),
    ]
    for col, item in zip(cols, values):
        with col: metric(*item)

    gain = n(adaptive.get("recall")) - n(static.get("recall"))
    saving = n(static.get("total_operational_cost")) - n(adaptive.get("total_operational_cost"))
    st.markdown(f'<div class="takeaway"><strong>Batch finding</strong><br>The Adaptive policy changes recall by <strong>{gain:+.2%}</strong> and operational cost by <strong>{money(-saving)}</strong> relative to Static Batch.</div>', unsafe_allow_html=True)

with comparison_tab:
    st.header("Static vs Adaptive Batch")
    rows = []
    for label, summary in [("Static Batch", static), ("Adaptive Batch", adaptive)]:
        rows.append({
            "Scenario": label,
            "Alerts": i(summary.get("selected_alerts")),
            "Frauds detected": i(summary.get("frauds_detected")),
            "Frauds missed": i(summary.get("frauds_missed")),
            "False positives": i(summary.get("false_positives")),
            "Precision": n(summary.get("precision")),
            "Recall": n(summary.get("recall")),
            "Operational cost": n(summary.get("total_operational_cost")),
        })
    frame = pd.DataFrame(rows)
    display = frame.copy()
    display["Precision"] = display["Precision"].map(lambda x: f"{x:.2%}")
    display["Recall"] = display["Recall"].map(lambda x: f"{x:.2%}")
    display["Operational cost"] = display["Operational cost"].map(money)
    st.dataframe(display, use_container_width=True, hide_index=True)

    a, b = st.columns(2)
    with a:
        st.markdown("### Fraud outcomes")
        st.bar_chart(frame.set_index("Scenario")[["Frauds detected", "Frauds missed"]], use_container_width=True)
    with b:
        st.markdown("### Recall and precision")
        st.bar_chart(frame.set_index("Scenario")[["Recall", "Precision"]], use_container_width=True)

with cost_tab:
    st.header("Cost and Workload Analysis")
    frame = pd.DataFrame([
        {"Scenario": "Static Batch", "Alerts": i(static.get("selected_alerts")), "Operational cost": n(static.get("total_operational_cost"))},
        {"Scenario": "Adaptive Batch", "Alerts": i(adaptive.get("selected_alerts")), "Operational cost": n(adaptive.get("total_operational_cost"))},
    ])
    a, b = st.columns(2)
    with a:
        st.markdown("### Alert workload")
        st.bar_chart(frame.set_index("Scenario")[["Alerts"]], use_container_width=True)
    with b:
        st.markdown("### Total operational cost")
        st.bar_chart(frame.set_index("Scenario")[["Operational cost"]], use_container_width=True)
    section_intro("How should cost be interpreted?", "Total operational cost combines investigation expenditure with the financial value of frauds that were not detected. Lower is better, but it must be interpreted together with recall and alert volume.")

with interpretation_tab:
    st.header("Research Interpretation")
    batch_gain = n(adaptive.get("recall")) - n(static.get("recall"))
    cost_difference = n(adaptive.get("total_operational_cost")) - n(static.get("total_operational_cost"))
    section_intro("Research focus", "Batch evaluation isolates policy quality. It does not model chronological congestion, per-step analyst capacity or repeat-alert suppression.")
    st.markdown(f"""
<div class="takeaway"><strong>RQ1 — Balance of detection, workload and cost</strong><br>
Adaptive Batch produced {i(adaptive.get('selected_alerts')):,} alerts, detected {i(adaptive.get('frauds_detected')):,} frauds and achieved {n(adaptive.get('recall')):.2%} recall.</div><br>
<div class="takeaway"><strong>RQ2 — Cost-aware logic versus a fixed threshold</strong><br>
Compared with Static Batch, recall changed by {batch_gain:+.2%} and total operational cost changed by {money(cost_difference)}.</div><br>
<div class="warning"><strong>Boundary of this dashboard</strong><br>
These results describe the policy's global potential. Whether the same advantage survives real chronological capacity constraints is evaluated separately in sequential_2nd_part.py.</div>
""", unsafe_allow_html=True)

with technical_tab:
    st.header("Technical Details")
    st.markdown("### Current API parameters")
    st.json(params)
    st.markdown("### Backend parameters")
    st.json(parameters)
    with st.expander("Show raw API response"):
        st.json(data)