from __future__ import annotations

import sys
from pathlib import Path
import html
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.dashboard.logic import (
    get_summary,
    i,
    n,
    normalise_windows,
    optional_i,
    trend_label,
)


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8002",
).rstrip("/")


SIMULATION_ENDPOINT = "simulation/sequential"


st.set_page_config(
    page_title="Fraud Decision Support — UX Evaluation",
    layout="wide",
)


# =========================================================
# VISUAL STYLE
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1400px;
        padding-top: 1.1rem;
        padding-bottom: 2.5rem;
    }

    .hero {
        padding: 1.25rem 1.4rem;
        border: 1px solid rgba(30,136,229,.28);
        border-radius: 16px;
        background:
            linear-gradient(
                135deg,
                rgba(25,118,210,.14),
                rgba(46,125,50,.07)
            );
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0 0 .45rem 0;
        font-size: 2rem;
    }

    .hero p {
        margin: 0;
        line-height: 1.55;
        opacity: .86;
    }

    .intro {
        padding: .95rem 1.05rem;
        border-left: 4px solid #1976d2;
        border-radius: 10px;
        background: rgba(25,118,210,.08);
        margin: .45rem 0 1rem;
        line-height: 1.5;
    }

    .metric-card {
        min-height: 150px;
        padding: 1rem;
        border: 1px solid rgba(128,128,128,.24);
        border-radius: 14px;
        background: rgba(128,128,128,.045);
    }

    .metric-card .value {
        font-size: 1.65rem;
        font-weight: 700;
        margin: .42rem 0 .3rem;
    }

    .funnel-card {
        min-height: 150px;
        padding: 1rem;
        border: 1px solid rgba(128,128,128,.24);
        border-radius: 14px;
        background: rgba(128,128,128,.04);
        text-align: center;
    }

    .funnel-card .number {
        font-size: 1.75rem;
        font-weight: 700;
        margin: .35rem 0;
    }

    .funnel-arrow {
        text-align: center;
        font-size: 1.55rem;
        opacity: .65;
        padding-top: 2.4rem;
    }

    .tone-blue { border-top: 4px solid #1976d2; }
    .tone-green { border-top: 4px solid #2e7d32; }
    .tone-orange { border-top: 4px solid #ef6c00; }
    .tone-red { border-top: 4px solid #c62828; }

    .story-card {
        padding: 1rem 1.05rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 14px;
        background: rgba(128,128,128,.035);
        min-height: 150px;
    }

    .question-card {
        padding: 1rem 1.05rem;
        border: 1px solid rgba(25,118,210,.25);
        border-radius: 14px;
        background: rgba(25,118,210,.055);
        margin: .5rem 0 1rem;
        line-height: 1.5;
    }

    .definition-card {
        padding: .9rem 1rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 12px;
        background: rgba(128,128,128,.03);
        min-height: 135px;
    }

    .takeaway {
        padding: 1rem 1.05rem;
        border-left: 5px solid #2e7d32;
        border-radius: 12px;
        background: rgba(46,125,50,.10);
        line-height: 1.5;
    }

    .warning {
        padding: 1rem 1.05rem;
        border-left: 5px solid #ef6c00;
        border-radius: 12px;
        background: rgba(239,108,0,.10);
        line-height: 1.5;
    }

    .workflow-step {
        padding: .85rem 1rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 12px;
        background: rgba(128,128,128,.035);
        text-align: center;
    }

    .arrow {
        text-align: center;
        font-size: 1.4rem;
        opacity: .7;
        margin: .2rem 0;
    }

    .small {
        font-size: .88rem;
        opacity: .73;
        line-height: 1.45;
    }

    div[data-testid="stSidebar"] .stExpander {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
    }
    
    .decision-box {
        padding: 1rem 1.1rem;
        border-left: 5px solid #8e44ad;
        border-radius: 12px;
        background: rgba(142,68,173,.10);
        margin: .6rem 0 1rem;
        line-height: 1.55;
    }

    .compact-note {
        padding: .9rem 1rem;
        border-radius: 12px;
        margin: .35rem 0;
        line-height: 1.5;
    }

    .section-divider {
        margin: 1.25rem 0;
        border-top: 1px solid rgba(128,128,128,.20);
    }

    .chart-conclusion {
        padding: .9rem 1rem;
        border-left: 4px solid #1976d2;
        border-radius: 10px;
        background: rgba(25,118,210,.08);
        line-height: 1.5;
        margin-top: .65rem;
        min-height: 92px;
    }

    .chart-spacer {
        height: 2.5rem;
    }

    .step-explanation {
        padding: 1rem 1.1rem;
        border: 1px solid rgba(25,118,210,.30);
        border-left: 5px solid #1976d2;
        border-radius: 12px;
        background: rgba(25,118,210,.08);
        line-height: 1.55;
        margin: .55rem 0 1.15rem;
    }


    .capacity-step-intro {
        padding: .9rem 1rem;
        border-left: 4px solid #1976d2;
        border-radius: 10px;
        background: rgba(25,118,210,.075);
        line-height: 1.5;
        margin: .45rem 0 .8rem;
    }

    .capacity-step-card {
        min-height: 118px;
        padding: .9rem 1rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 12px;
        background: rgba(128,128,128,.035);
        line-height: 1.45;
    }

    .capacity-step-card .step-value {
        font-size: 1.15rem;
        font-weight: 700;
        margin: .35rem 0;
    }
    </style>
    
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================




def money(value: Any) -> str:
    return f"€{n(value):,.2f}"


def pct(value: Any, decimals: int = 1) -> str:
    return f"{n(value):.{decimals}%}"


def intro(title: str, text: str) -> None:
    st.markdown(
        (
            '<div class="intro">'
            f"<strong>{html.escape(title)}</strong><br>"
            f"{html.escape(text)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def metric_card(
    title: str,
    value: str,
    note: str,
    tone: str = "blue",
) -> None:
    st.markdown(
        f"""
        <div class="metric-card tone-{html.escape(tone)}">
            <strong>{html.escape(title)}</strong>
            <div class="value">{html.escape(value)}</div>
            <div class="small">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def question_card(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="question-card">
            <strong>{html.escape(title)}</strong><br>
            {html.escape(text)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def funnel_card(
    title: str,
    value: str,
    explanation: str,
) -> None:
    st.markdown(
        f"""
        <div class="funnel-card">
            <strong>{html.escape(title)}</strong>
            <div class="number">{html.escape(value)}</div>
            <div class="small">{html.escape(explanation)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def concept_card(
    title: str,
    text: str,
    footer: str = "",
) -> None:
    """Render a simple educational concept card."""
    footer_html = (
        f'<div class="small">{html.escape(footer)}</div>'
        if footer
        else ""
    )

    st.markdown(
        f"""
        <div class="definition-card">
            <strong>{html.escape(title)}</strong>
            <p>{html.escape(text)}</p>
            {footer_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def definition_card(
    title: str,
    meaning: str,
    why_it_matters: str,
) -> None:
    st.markdown(
        f"""
        <div class="definition-card">
            <strong>{html.escape(title)}</strong>
            <p>{html.escape(meaning)}</p>
            <div class="small">
                <strong>Why it matters:</strong>
                {html.escape(why_it_matters)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_step(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="workflow-step">
            <strong>{html.escape(title)}</strong><br>
            <span class="small">{html.escape(text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def arrow() -> None:
    st.markdown(
        '<div class="arrow">↓</div>',
        unsafe_allow_html=True,
    )



    result = frame.copy().rename(
        columns={
            "monitoring_window": "window",
            "selected_alerts": "accepted_alerts",
            "suppressed_alerts": "suppressed",
            "capacity_rejected_alerts": "capacity_rejected",
            "policy_candidate_alerts": "candidate_alerts",
            "total_operational_cost": "operational_cost",
        }
    )

    if "window" in result.columns:
        result = result.sort_values("window")

    return result


@st.cache_data(ttl=60, show_spinner=False)
def load_data(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{API_BASE_URL}/{SIMULATION_ENDPOINT}",
        params=params,
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600, show_spinner=False)
def load_sensitivity_data(
    base_params: dict[str, Any],
    cache_schema_version: str = "operational-flow-v2",
) -> dict[str, Any]:
    """
    Run all sensitivity experiments through one optimized API request.

    The schema version is intentionally part of the cache key so a dashboard
    release that needs new API fields cannot silently reuse an older payload.
    """
    endpoint_params = {
        "limit": int(base_params["limit"]),
        "investigation_cost": float(base_params["investigation_cost"]),
        "static_threshold": float(base_params["static_threshold"]),
        "ranking_policy": str(base_params["ranking_policy"]),
        "risk_zone_floor": float(base_params["risk_zone_floor"]),
        "budget_multiplier": float(base_params["budget_multiplier"]),
        "alert_budget_per_step": int(base_params["alert_budget_per_step"]),
        "suppression_window": int(base_params["suppression_window"]),
        "monitoring_window_size": int(base_params["monitoring_window_size"]),
    }

    response = requests.get(
        f"{API_BASE_URL}/simulation/sensitivity",
        params=endpoint_params,
        timeout=900,
    )
    response.raise_for_status()
    return response.json()


def prepare_sensitivity_results(
    payload: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Convert the optimized endpoint response to the dashboard's display format."""
    grouped: dict[str, list[dict[str, Any]]] = {}

    for row in payload.get("results", []):
        # The UX evaluation reports transaction-volume scenarios up to 10,000
        # transactions. Ignore any larger legacy result returned by the backend.
        if (
            str(row.get("experiment", "")) == "Transaction volume"
            and n(row.get("tested_value")) > 10000
        ):
            continue

        static_recall = n(row.get("static_recall"))
        adaptive_recall = n(row.get("adaptive_recall"))
        static_cost = n(row.get("static_operational_cost"))
        adaptive_cost = n(row.get("adaptive_operational_cost"))

        # Preserve the dashboard's existing, easy-to-explain comparison rule.
        if adaptive_recall > static_recall + 1e-9:
            winner = "Adaptive"
        elif static_recall > adaptive_recall + 1e-9:
            winner = "Static"
        elif adaptive_cost < static_cost - 0.01:
            winner = "Adaptive"
        elif static_cost < adaptive_cost - 0.01:
            winner = "Static"
        else:
            winner = "Tie"

        experiment_name = str(row.get("experiment", "Unknown experiment"))
        grouped.setdefault(experiment_name, []).append(
            {
                "experiment": experiment_name,
                "parameter": row.get("api_parameter"),
                "value": row.get("tested_value"),
                "static_recall": static_recall,
                "adaptive_recall": adaptive_recall,
                "recall_difference": adaptive_recall - static_recall,
                "static_cost": static_cost,
                "adaptive_cost": adaptive_cost,
                "adaptive_cost_saving": static_cost - adaptive_cost,
                "static_investigated": i(row.get("static_selected_alerts")),
                "adaptive_investigated": i(row.get("adaptive_selected_alerts")),
                "static_detected": i(row.get("static_frauds_detected")),
                "adaptive_detected": i(row.get("adaptive_frauds_detected")),
                "static_candidates": optional_i(row.get("static_policy_candidate_alerts")),
                "adaptive_candidates": optional_i(row.get("adaptive_policy_candidate_alerts")),
                "static_suppressed": optional_i(row.get("static_suppressed_alerts")),
                "adaptive_suppressed": optional_i(row.get("adaptive_suppressed_alerts")),
                "static_overflow": optional_i(row.get("static_capacity_rejected_alerts")),
                "adaptive_overflow": optional_i(row.get("adaptive_capacity_rejected_alerts")),
                "winner": winner,
            }
        )

    for rows in grouped.values():
        rows.sort(key=lambda item: float(item["value"]))

    return grouped


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>Fraud Decision Support Dashboard</h1>
        <p>
            Research prototype for evaluating how machine-learning fraud scores can be
            translated into prioritised human-investigation decisions under limited
            analyst capacity.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="info-box" style="margin-top:.65rem; margin-bottom:.85rem;">
        <strong>About this prototype</strong><br>
        <strong>Dataset:</strong>
        synthetic <a href="https://www.kaggle.com/datasets/ealaxi/paysim1/data" target="_blank">PaySim mobile-money transactions</a>
        &nbsp;·&nbsp;
        <strong>Evaluation:</strong> offline chronological replay
        &nbsp;·&nbsp;
        <strong>Purpose:</strong> decision-support research, not live payment validation.<br>
        <span class="small">
            <strong>Dataset source:</strong> Kaggle PaySim dataset.
            It does not process live banking or UPI transactions. Transaction IDs and
            simulated entity identifiers shown in the dashboard do not correspond to real
            customers, cards, accounts or payment identifiers.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("Simulation settings")
st.sidebar.caption(
    "The controls below change the simulated operating scenario."
)

with st.sidebar.expander(
    "Main controls",
    expanded=True,
):
    transaction_limit = st.selectbox(
        "Transactions evaluated",
        [1000, 3000, 10000],
        index=2,
        help=(
            "How many transactions are included in the current simulation."
        ),
    )

    alert_budget_per_step = st.number_input(
        "Analyst capacity (alerts per operational step)",
        min_value=1,
        max_value=5000,
        value=50,
        step=5,
        help=(
            "Maximum number of alerts that can enter human investigation in each "
            "operational step. Increase or decrease this value to test how analyst "
            "resources affect overflow, workload and fraud coverage."
        ),
    )

    suppression_window = st.number_input(
        "Repeat-alert suppression window",
        min_value=0,
        max_value=100,
        value=3,
        step=1,
        help=(
            "For how many following steps repeated alerts for the same "
            "entity may be filtered to avoid duplicate work."
        ),
    )

with st.sidebar.expander(
    "Advanced controls",
    expanded=False,
):
    investigation_cost = st.number_input(
        "Assumed cost per investigation (€)",
        min_value=0.0,
        value=10.0,
        step=1.0,
        help="Experimental assumption: estimated cost assigned to reviewing one alert. This is not an observed banking cost.",
    )

    static_threshold = st.slider(
        "Static fraud threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
        help=(
            "Fixed fraud-score threshold used by the Static policy."
        ),
    )

    risk_zone_floor = st.slider(
        "Minimum Adaptive fraud threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.30,
        step=0.01,
        help=(
            "Minimum fraud-score threshold required for a transaction to "
            "enter the Adaptive risk zone."
        ),
    )

    budget_multiplier = st.slider(
        "Adaptive threshold budget multiplier",
        min_value=0.5,
        max_value=2.5,
        value=1.4,
        step=0.1,
        help=(
            "Controls how broadly the Adaptive policy expands its "
            "candidate-alert budget after the minimum threshold is applied."
        ),
    )

if st.sidebar.button(
    "Refresh results",
    width="stretch",
):
    st.cache_data.clear()

st.sidebar.divider()
st.sidebar.markdown(
    """
    **Suggested reading order**

    1. Executive Summary  
    2. Analyst Capacity  
    3. Sequential Workflow  
    4. Monitoring  
    5. Sensitivity Analysis
    """
)
st.sidebar.caption(f"API: `{API_BASE_URL}`")

st.sidebar.markdown(
    """
    <div style="
        padding: .75rem .8rem;
        border-left: 3px solid #1976d2;
        border-radius: 8px;
        background: rgba(25,118,210,.08);
        font-size: .84rem;
        line-height: 1.45;
        margin-top: .5rem;
    ">
        <strong>Experiment rule</strong><br>
        Change one parameter at a time so that the cause of each result remains clear.
        Use the help buttons beside the controls for short explanations.
    </div>
    """,
    unsafe_allow_html=True,
)



params = {
    "limit": int(transaction_limit),
    "investigation_cost": float(investigation_cost),
    "static_threshold": float(static_threshold),
    "ranking_policy": "risk_zone",
    "risk_zone_floor": float(risk_zone_floor),
    "alert_rate_low": 0.03,
    "alert_rate_high": 0.10,
    "budget_multiplier": float(budget_multiplier),
    "alert_budget_per_step": int(alert_budget_per_step),
    "suppression_window": int(suppression_window),
    "monitoring_window_size": 1000,
}


# =========================================================
# API REQUEST
# =========================================================

try:
    with st.spinner("Loading the current simulation..."):
        data = load_data(params)
except requests.exceptions.ConnectionError:
    st.error(
        "FastAPI is not available. Run:\n\n"
        "`py -m uvicorn app.api.main:app --reload --port 8002`"
    )
    st.stop()
except requests.exceptions.Timeout:
    st.error(
        "The API request timed out. Try a smaller transaction volume."
    )
    st.stop()
except requests.exceptions.RequestException as exc:
    st.error("The API request failed.")
    st.exception(exc)
    st.stop()


static_batch = get_summary(data, "static_batch")
adaptive_batch = get_summary(data, "adaptive_batch")
static_seq = get_summary(data, "static_sequential")
adaptive_seq = get_summary(data, "adaptive_sequential")
parameters = data.get("parameters", {})

adaptive_windows = normalise_windows(
    pd.DataFrame(
        data.get("adaptive_sequential", {}).get(
            "monitoring_windows",
            [],
        )
    )
)


# =========================================================
# TABS
# =========================================================

(
    executive_tab,
    capacity_tab,
    workflow_tab,
    monitoring_tab,
    sensitivity_tab,
) = st.tabs(
    [
        "1. Executive Summary",
        "2. Analyst Capacity",
        "3. Sequential Workflow",
        "4. Monitoring",
        "5. Sensitivity Analysis",
    ]
)


# =========================================================
# 2. EXECUTIVE SUMMARY
# =========================================================

with executive_tab:
    st.header("Executive Summary")

    st.markdown(
        """
        <div class="info-box">
            <strong>Decision question</strong><br>
            Which alert-selection policy provides the stronger operational outcome
            when fraud coverage, analyst workload and estimated cost are considered together?
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        """
        **Quick guide**

        Start with the **Executive Summary** for the main Static vs Adaptive result.  
        Use **Analyst Capacity** to see which alerts enter the investigation queue and why.  
        Open **Sequential Workflow** to understand how transactions are processed over time.  
        Use **Monitoring** to inspect changes across the replay, and **Sensitivity Analysis** to test how different operating assumptions affect the results.

        **Tip:** When comparing scenarios, change one setting at a time so that the effect of each operational assumption remains clear.
        """
    )

    total_frauds = i(
        adaptive_batch.get(
            "total_frauds",
            i(adaptive_batch.get("frauds_detected"))
            + i(adaptive_batch.get("frauds_missed")),
        )
    )

    static_batch_frauds = i(static_batch.get("frauds_detected"))
    adaptive_batch_frauds = i(adaptive_batch.get("frauds_detected"))
    static_seq_frauds = i(static_seq.get("frauds_detected"))
    adaptive_seq_frauds = i(adaptive_seq.get("frauds_detected"))
    static_batch_alerts = i(static_batch.get("selected_alerts"))
    adaptive_batch_alerts = i(adaptive_batch.get("selected_alerts"))
    static_investigated_alerts = i(static_seq.get("selected_alerts"))
    adaptive_investigated_alerts = i(adaptive_seq.get("selected_alerts"))

    static_seq_recall = n(static_seq.get("recall"))
    adaptive_seq_recall = n(adaptive_seq.get("recall"))
    static_seq_precision = n(static_seq.get("precision"))
    adaptive_seq_precision = n(adaptive_seq.get("precision"))

    static_seq_investigation_cost = n(static_seq.get("investigation_cost_total"))
    adaptive_seq_investigation_cost = n(adaptive_seq.get("investigation_cost_total"))
    static_seq_missed_fraud_cost = n(static_seq.get("missed_fraud_cost"))
    adaptive_seq_missed_fraud_cost = n(adaptive_seq.get("missed_fraud_cost"))
    static_seq_missed_frauds = i(static_seq.get("frauds_missed"))
    adaptive_seq_missed_frauds = i(adaptive_seq.get("frauds_missed"))
    static_seq_total_cost = n(static_seq.get("total_operational_cost"))
    adaptive_seq_total_cost = n(adaptive_seq.get("total_operational_cost"))

    sequential_cost_saving = static_seq_total_cost - adaptive_seq_total_cost
    sequential_recall_gain = adaptive_seq_recall - static_seq_recall
    seq_fraud_gain = adaptive_seq_frauds - static_seq_frauds

    
    

    # --------------------------------------------------------
    # Overall outcome — compact layout retained from the screen
    # the user preferred.
    # --------------------------------------------------------
    st.markdown("### Overall outcome")

    if sequential_recall_gain > 0 and sequential_cost_saving > 0:
        preferred_policy = "Adaptive"
        recommendation = (
            "Adaptive is preferred under the current operating configuration because it "
            "achieves higher Sequential recall while also producing a lower estimated "
            "operational cost."
        )
        recommendation_tone = "green"
    elif sequential_recall_gain > 0:
        preferred_policy = "Adaptive"
        recommendation = (
            "Adaptive improves fraud coverage under the current operating configuration, "
            "but management should review the additional estimated cost or workload."
        )
        recommendation_tone = "orange"
    elif sequential_recall_gain < 0:
        preferred_policy = "Static"
        recommendation = (
            "Static currently achieves higher Sequential recall. Adaptive settings should "
            "be reviewed before it is preferred operationally."
        )
        recommendation_tone = "orange"
    elif sequential_cost_saving > 0:
        preferred_policy = "Adaptive"
        recommendation = (
            "The policies achieve equal Sequential recall, but Adaptive produces the lower "
            "estimated operational cost under the current assumptions."
        )
        recommendation_tone = "green"
    elif sequential_cost_saving < 0:
        preferred_policy = "Static"
        recommendation = (
            "The policies achieve equal Sequential recall, so Static is preferred because "
            "it produces the lower estimated operational cost."
        )
        recommendation_tone = "orange"
    else:
        preferred_policy = "No clear winner"
        recommendation = (
            "The policies are operationally equivalent on the current recall and estimated "
            "cost criteria."
        )
        recommendation_tone = "blue"

    k1, k2 = st.columns([1, 2])

    with k1:
        metric_card(
            "Recommended policy",
            preferred_policy,
            "Preferred policy under the current operational scenario.",
            recommendation_tone,
        )

    with k2:
        if sequential_cost_saving >= 0:
            cost_advantage_text = f"{money(sequential_cost_saving)} lower estimated cost"
        else:
            cost_advantage_text = f"{money(abs(sequential_cost_saving))} higher estimated cost"

        operational_advantage = (
            f"{sequential_recall_gain * 100:+.1f}% recall · "
            f"{seq_fraud_gain:+,} frauds detected · "
            f"{cost_advantage_text}"
        )

        metric_card(
            "Operational advantage",
            operational_advantage,
            "Adaptive performance under the current Sequential operating scenario.",
            "green" if sequential_recall_gain > 0 and sequential_cost_saving > 0 else "orange",
        )

    st.markdown(
        f"""
        <div class="decision-box">
            <strong>Management recommendation</strong><br>
            {html.escape(recommendation)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Main operational comparison — Sequential only.
    # --------------------------------------------------------
    st.markdown("### Why is this policy preferred?")

    sequential_comparison = pd.DataFrame(
        [
            {
                "Policy": "Static",
                "Investigated alerts": static_investigated_alerts,
                "Frauds detected": static_seq_frauds,
                "Frauds missed": static_seq_missed_frauds,
                "Precision": static_seq_precision,
                "Recall": static_seq_recall,
                "Estimated operational cost (€)": static_seq_total_cost,
            },
            {
                "Policy": "Adaptive",
                "Investigated alerts": adaptive_investigated_alerts,
                "Frauds detected": adaptive_seq_frauds,
                "Frauds missed": adaptive_seq_missed_frauds,
                "Precision": adaptive_seq_precision,
                "Recall": adaptive_seq_recall,
                "Estimated operational cost (€)": adaptive_seq_total_cost,
            },
        ]
    )

    sequential_display = sequential_comparison.copy()
    sequential_display["Precision"] = sequential_display["Precision"].map(pct)
    sequential_display["Recall"] = sequential_display["Recall"].map(pct)
    sequential_display["Estimated operational cost (€)"] = (
        sequential_display["Estimated operational cost (€)"].map(money)
    )

    st.dataframe(
        sequential_display,
        width="stretch",
        hide_index=True,
    )

    # Batch is retained, but only as a secondary methodological reference.
    with st.expander("Methodological reference: ideal Batch baseline", expanded=False):
        st.markdown(
            """
            Batch results are retained only as an ideal reference before chronology,
            suppression and per-step analyst-capacity constraints are introduced.
            The main dashboard conclusions are based on the Sequential operational replay.
            """
        )

        batch_reference = pd.DataFrame(
            [
                {
                    "Policy": "Static",
                    "Alerts": static_batch_alerts,
                    "Frauds detected": static_batch_frauds,
                    "Frauds missed": i(static_batch.get("frauds_missed")),
                    "Precision": n(static_batch.get("precision")),
                    "Recall": n(static_batch.get("recall")),
                },
                {
                    "Policy": "Adaptive",
                    "Alerts": adaptive_batch_alerts,
                    "Frauds detected": adaptive_batch_frauds,
                    "Frauds missed": i(adaptive_batch.get("frauds_missed")),
                    "Precision": n(adaptive_batch.get("precision")),
                    "Recall": n(adaptive_batch.get("recall")),
                },
            ]
        )

        batch_reference_display = batch_reference.copy()
        batch_reference_display["Precision"] = batch_reference_display["Precision"].map(pct)
        batch_reference_display["Recall"] = batch_reference_display["Recall"].map(pct)

        st.dataframe(
            batch_reference_display,
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "Batch asks what the policies could detect under ideal evaluation conditions; "
            "Sequential replay asks what can actually reach investigation once operational "
            "constraints are enforced."
        )

    # --------------------------------------------------------
    # Detailed cost section — retained from the older dashboard.
    # --------------------------------------------------------
    st.markdown("### Cost impact in the Sequential simulation")

    cost_kpi_col, cost_explanation_col = st.columns([1, 2.25])

    with cost_kpi_col:
        if sequential_cost_saving >= 0:
            metric_card(
                "Estimated cost avoided by Adaptive",
                money(sequential_cost_saving),
                "Static estimated cost minus Adaptive estimated cost in the Sequential replay.",
                "green",
            )
        else:
            metric_card(
                "Estimated additional cost of Adaptive",
                money(abs(sequential_cost_saving)),
                "Adaptive estimated cost minus Static estimated cost in the Sequential replay.",
                "orange",
            )

    with cost_explanation_col:
        st.markdown(
            f"""
            <div class="question-card">
                <strong>What do these euro amounts mean?</strong><br>
                They are <strong>simulation-based estimates</strong>, not observed bank losses.
                For each policy, estimated operational cost is the sum of the cost of
                investigated alerts and the transaction amounts of fraud cases that were
                missed under the current simulation assumptions. The current assumed review
                cost is <strong>{money(investigation_cost)}</strong> per investigated alert.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("How was estimated operational cost calculated?", expanded=False):

        st.markdown(
            f"""
            <div class="question-card">
                <strong>Formula used in this simulation</strong><br><br>
                <strong>Estimated operational cost</strong> = investigation cost + estimated value of missed fraud<br>
                <strong>Investigation cost</strong> = investigated alerts × assumed review cost
                ({money(investigation_cost)} per alert)<br>
                <strong>Estimated value of missed fraud</strong> = sum of the <code>amount</code> values
                of fraud transactions that were missed.<br><br>
                The transaction amount is used as a <strong>proxy for direct financial loss</strong>.
                These are experimental simulation estimates, not observed bank accounting losses.
            </div>
            """,
            unsafe_allow_html=True,
        )

        static_missed_share = (
            static_seq_missed_fraud_cost / static_seq_total_cost
            if static_seq_total_cost else 0.0
        )
        adaptive_missed_share = (
            adaptive_seq_missed_fraud_cost / adaptive_seq_total_cost
            if adaptive_seq_total_cost else 0.0
        )

        cost_breakdown = pd.DataFrame(
            [
                {
                    "Policy": "Static Sequential",
                    "Investigation-cost calculation": (
                        f"{static_investigated_alerts:,} × {money(investigation_cost)}"
                    ),
                    "Investigation cost (€)": static_seq_investigation_cost,
                    "Estimated missed-fraud value (€)": static_seq_missed_fraud_cost,
                    "Missed-fraud share of total cost": static_missed_share,
                    "Total estimated operational cost (€)": static_seq_total_cost,
                    "Difference vs Static (€)": 0.0,
                },
                {
                    "Policy": "Adaptive Sequential",
                    "Investigation-cost calculation": (
                        f"{adaptive_investigated_alerts:,} × {money(investigation_cost)}"
                    ),
                    "Investigation cost (€)": adaptive_seq_investigation_cost,
                    "Estimated missed-fraud value (€)": adaptive_seq_missed_fraud_cost,
                    "Missed-fraud share of total cost": adaptive_missed_share,
                    "Total estimated operational cost (€)": adaptive_seq_total_cost,
                    "Difference vs Static (€)": adaptive_seq_total_cost - static_seq_total_cost,
                },
            ]
        )

        cost_breakdown_display = cost_breakdown.copy()

        for cost_column in [
            "Investigation cost (€)",
            "Estimated missed-fraud value (€)",
            "Total estimated operational cost (€)",
            "Difference vs Static (€)",
        ]:
            cost_breakdown_display[cost_column] = (
                cost_breakdown_display[cost_column].map(money)
            )

        cost_breakdown_display["Missed-fraud share of total cost"] = (
            cost_breakdown_display["Missed-fraud share of total cost"].map(
                lambda value: f"{value:.1%}"
            )
        )

        st.dataframe(
            cost_breakdown_display,
            width="stretch",
            hide_index=True,
        )

        st.caption(
            "The table focuses only on the cost calculation. The investigation-cost column shows "
            "how review cost is derived, while the missed-fraud share indicates which component "
            "drives the total estimated operational cost."
        )

    st.markdown(
        """
        <div class="takeaway">
            <strong>Decision implication</strong><br>
            Adaptive uses the available investigation capacity more effectively,
            improving fraud coverage without increasing overall operational cost.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Learn more: concepts and definitions"):
        st.markdown(
            """
            **Adaptive threshold budget multiplier:** controls how broadly the
            Adaptive policy may expand its candidate-alert budget after the minimum
            Adaptive fraud threshold is applied. Higher values may generate more
            candidate alerts before analyst capacity is enforced.

            **Alerts allowed per operational step:** the configurable maximum number
            of alerts that may enter the analyst queue during each operational step.

            **Analyst capacity:** the overall investigation capability of the analyst
            team. In this simulation, it is represented by the configured
            **Alerts allowed per operational step** value.

            **Analyst queue:** the list of eligible alerts accepted for human
            investigation after prioritisation and analyst-capacity limits are applied.

            **Batch evaluation:** an ideal methodological reference that measures policy
            performance before chronological replay, suppression and per-step analyst-capacity
            constraints are applied.

            **Budget overflow:** eligible alerts that could not enter the analyst queue
            because the analyst-capacity limit for that operational step had already
            been reached.

            **Candidate alert:** a transaction proposed by the decision policy before
            suppression and analyst-capacity constraints are applied.

            **Eligible alert:** a candidate alert that remains after suppression and
            can therefore compete for analyst capacity.

            **Investigated alert:** an eligible alert that enters the analyst queue for
            human review.

            **Investigation cost:** the assumed financial cost of reviewing one alert.

            **Minimum Adaptive fraud threshold:** the lowest fraud-risk score that a
            transaction must reach before it can be considered by the Adaptive policy.

            **Monitoring window:** a reporting interval used to aggregate dashboard
            statistics. It is separate from an operational step and does not control
            analyst-capacity resets.

            **Estimated operational cost:** a simulation-based measure equal to the
            investigation cost plus the estimated missed-fraud loss. Investigation cost is
            calculated as investigated alerts × assumed cost per investigation. In the current
            implementation, missed-fraud loss is based on the transaction amounts of fraud
            cases that were not detected. It is an experimental decision-support measure, not
            an observed bank accounting figure.

            **Estimated cost avoided by Adaptive:** Static Sequential estimated operational
            cost minus Adaptive Sequential estimated operational cost. A positive value means
            Adaptive produces the lower simulated cost under the current assumptions.

            **Operational step:** one chronological decision cycle of the Sequential
            replay. Suppression, ranking and analyst capacity are applied independently
            within each step before the replay continues.

            **Precision:** the share of investigated alerts that were truly fraudulent.

            **Recall:** the share of all real fraud cases detected.

            **Robustness:** the ability of the decision layer to produce reasonable and
            explainable results across different operational configurations.

            **Sensitivity analysis:** evaluates how system behaviour changes when one
            operational parameter is modified while the remaining settings stay fixed.

            **Sequential simulation:** the primary operational evaluation used by this
            dashboard. It measures fraud-policy performance after chronology, suppression,
            prioritisation and limited analyst capacity are introduced.

            **Static fraud threshold:** the fixed fraud-risk score above which a
            transaction becomes a candidate alert under the Static policy.

            **Suppression:** filters repeated alerts for the same simulated entity
            within the configured suppression window before analyst capacity is applied.

            **Trade-off:** a situation where one policy improves one objective while
            worsening another, such as higher recall with higher cost.

            **Transaction volume:** the number of historical transactions included in
            one simulation experiment.
            """
        )

    with st.expander("Technical details"):
        st.markdown("#### Experimental dataset")
        st.markdown(
            """
            **Dataset:** PaySim synthetic payment transaction dataset  
            **Evaluation mode:** Offline historical replay  
            **Primary operational evaluation:** Chronological Sequential simulation using the dataset's `step` variable  
            **Ideal reference:** Batch policy evaluation before operational constraints  
            **Purpose:** Evaluation of fraud-detection and operational decision-making strategies under controlled experimental conditions  
            **Environment:** Research prototype; the results do not originate from a live banking production system

            All experiments presented in this dashboard use PaySim transactions.
            The same experimental dataset and baseline configuration are used across
            policy comparisons unless a sensitivity experiment explicitly changes the
            transaction volume or another operating parameter.
            """
        )

        st.divider()
        st.markdown("#### Current result summary")
        st.json(
            {
                "dataset": "PaySim",
                "evaluation_mode": "offline chronological replay",
                "environment": "research prototype",
                "total_frauds": total_frauds,
                "static_sequential_frauds": static_seq_frauds,
                "adaptive_sequential_frauds": adaptive_seq_frauds,
                "adaptive_investigated_alerts": adaptive_investigated_alerts,
                "batch_reference_available": True,
            }
        )


# =========================================================
# 3. ANALYST CAPACITY
# =========================================================

with capacity_tab:
    st.header("Analyst Capacity by Policy")

    st.caption(
        "Select a policy to see how candidate alerts move through suppression, "
        "prioritisation and the per-step analyst-capacity limit."
    )

    policy_choice = st.radio(
        "Policy",
        ["Static", "Adaptive"],
        horizontal=True,
        key="capacity_policy_choice",
    )

    selected_summary = (
        static_seq
        if policy_choice == "Static"
        else adaptive_seq
    )

    selected_payload = (
        data.get("static_sequential", {})
        if policy_choice == "Static"
        else data.get("adaptive_sequential", {})
    )

    candidates = i(selected_summary.get("policy_candidate_alerts"))
    accepted = i(selected_summary.get("selected_alerts"))
    suppressed = i(selected_summary.get("suppressed_alerts"))
    rejected = i(selected_summary.get("capacity_rejected_alerts"))
    eligible_after_suppression = max(candidates - suppressed, 0)

    unique_steps = i(parameters.get("unique_steps"))
    maximum_capacity = i(
        parameters.get(
            "maximum_sequential_capacity",
            int(alert_budget_per_step) * unique_steps,
        )
    )

    # ---------------------------------------------------------
    # POLICY-LEVEL CAPACITY OUTCOMES
    # ---------------------------------------------------------
    k1, k2, k3 = st.columns(3)

    with k1:
        metric_card(
            "Investigated alerts",
            f"{accepted:,}",
            "Alerts that entered the human-investigation queue.",
            "green",
        )

    with k2:
        metric_card(
            "Suppressed alerts",
            f"{suppressed:,}",
            "Repeated alerts filtered before analyst capacity was used.",
            "orange",
        )

    with k3:
        metric_card(
            "Capacity-rejected alerts",
            f"{rejected:,}",
            "Eligible alerts that could not be investigated because the step limit was full.",
            "red",
        )

    # ---------------------------------------------------------
    # FRAUD INVESTIGATION FUNNEL — directly under policy KPIs
    # ---------------------------------------------------------
    st.markdown("### Fraud Investigation Funnel")

    frauds_detected = i(selected_summary.get("frauds_detected"))
    frauds_missed = i(selected_summary.get("frauds_missed"))
    false_positives = i(selected_summary.get("false_positives"))
    total_transactions = i(
        selected_summary.get("total_transactions", transaction_limit)
    )

    funnel_rows = pd.DataFrame(
        [
            {"Stage": "Transactions evaluated", "Count": total_transactions},
            {"Stage": "Candidate alerts", "Count": candidates},
            {"Stage": "Eligible after suppression", "Count": eligible_after_suppression},
            {"Stage": "Investigated alerts", "Count": accepted},
            {"Stage": "Frauds detected", "Count": frauds_detected},
        ]
    )

    st.bar_chart(
        funnel_rows.set_index("Stage")[["Count"]],
        width="stretch",
    )

    funnel_col1, funnel_col2, funnel_col3 = st.columns(3)
    with funnel_col1:
        metric_card(
            "Frauds detected",
            f"{frauds_detected:,}",
            "Investigated alerts confirmed as fraud in the evaluation labels (TP).",
            "green",
        )
    with funnel_col2:
        metric_card(
            "Frauds missed",
            f"{frauds_missed:,}",
            "Fraud transactions that did not reach investigation (FN).",
            "red",
        )
    with funnel_col3:
        metric_card(
            "Non-fraud alerts investigated",
            f"{false_positives:,}",
            "Investigated alerts that were non-fraud in the evaluation labels (FP).",
            "orange",
        )

    st.caption(
        f"Alert does not mean confirmed fraud: {accepted:,} alerts were investigated under "
        f"the current {policy_choice} scenario, while {frauds_detected:,} were fraud in the "
        "PaySim evaluation labels."
    )

    # ---------------------------------------------------------
    # OPERATIONAL STEP BREAKDOWN — one concise explanation only
    # ---------------------------------------------------------
    st.markdown("### Analyst capacity by operational step")
    st.caption(
        f"Each PaySim step is treated as one decision cycle. Up to "
        f"{int(alert_budget_per_step)} eligible alerts can be investigated in each step; "
        "unused capacity is not carried to the next step."
    )

    step_records = selected_payload.get("operational_steps", [])
    step_frame = pd.DataFrame(step_records)

    if step_frame.empty:
        st.info(
            "No operational-step records were returned by the API. Restart FastAPI after "
            "loading the updated sequential simulation files."
        )
    else:
        required_step_columns = {
            "step",
            "candidate_alerts",
            "suppressed_alerts",
            "eligible_alerts",
            "investigated_alerts",
            "capacity_rejected_alerts",
            "unused_capacity",
        }
        missing_step_columns = sorted(
            required_step_columns - set(step_frame.columns)
        )

        if missing_step_columns:
            st.warning(
                "Operational-step data are missing fields: "
                f"{missing_step_columns}"
            )
        else:
            step_frame = step_frame.sort_values("step").reset_index(drop=True)

            step_breakdown = pd.DataFrame(
                {
                    "Step": step_frame["step"].map(i),
                    "Candidate": step_frame["candidate_alerts"].map(i),
                    "Suppressed": step_frame["suppressed_alerts"].map(i),
                    "Eligible": step_frame["eligible_alerts"].map(i),
                    "Capacity": int(alert_budget_per_step),
                    "Investigated": step_frame["investigated_alerts"].map(i),
                    "Capacity rejected": step_frame[
                        "capacity_rejected_alerts"
                    ].map(i),
                    "Unused capacity": step_frame["unused_capacity"].map(i),
                }
            )

            totals_row = pd.DataFrame(
                [
                    {
                        "Step": "Total",
                        "Candidate": int(step_breakdown["Candidate"].sum()),
                        "Suppressed": int(step_breakdown["Suppressed"].sum()),
                        "Eligible": int(step_breakdown["Eligible"].sum()),
                        "Capacity": int(step_breakdown["Capacity"].sum()),
                        "Investigated": int(step_breakdown["Investigated"].sum()),
                        "Capacity rejected": int(
                            step_breakdown["Capacity rejected"].sum()
                        ),
                        "Unused capacity": int(
                            step_breakdown["Unused capacity"].sum()
                        ),
                    }
                ]
            )

            step_breakdown = pd.concat(
                [step_breakdown, totals_row],
                ignore_index=True,
            )
            step_breakdown["Step"] = step_breakdown["Step"].astype(str)

            st.dataframe(
                step_breakdown,
                width="stretch",
                hide_index=True,
            )

    # ---------------------------------------------------------
    # TRANSACTION-LEVEL DATA PREPARATION
    # ---------------------------------------------------------
    decision_rows = selected_payload.get("decision_rows", [])
    queue_frame = pd.DataFrame(decision_rows)

    if queue_frame.empty:
        st.warning(
            "Transaction-level queue rows were not returned by the API. Use the queue-enabled "
            "simulation API and restart FastAPI."
        )
    else:
        for bool_column in [
            "policy_alert_candidate",
            "selected_alert",
            "suppression_applied",
            "capacity_rejected",
        ]:
            if bool_column in queue_frame.columns:
                queue_frame[bool_column] = (
                    queue_frame[bool_column].fillna(False).astype(bool)
                )

        queue_frame["Outcome"] = "Candidate"
        if "selected_alert" in queue_frame.columns:
            queue_frame.loc[
                queue_frame["selected_alert"], "Outcome"
            ] = "Investigate"
        if "suppression_applied" in queue_frame.columns:
            queue_frame.loc[
                queue_frame["suppression_applied"], "Outcome"
            ] = "Suppressed"
        if "capacity_rejected" in queue_frame.columns:
            queue_frame.loc[
                queue_frame["capacity_rejected"], "Outcome"
            ] = "Capacity reached"

        def queue_reason(row: pd.Series) -> str:
            outcome = str(row.get("Outcome", "Candidate"))
            priority = row.get("candidate_priority_rank")
            priority_text = (
                f"priority #{int(priority)} in step {i(row.get('step'))}"
                if pd.notna(priority)
                else "its policy ranking"
            )

            if outcome == "Investigate":
                return (
                    f"Eligible candidate with {priority_text}; analyst capacity was still available."
                )
            if outcome == "Suppressed":
                return (
                    "Removed from investigation because a previously accepted alert for the same "
                    "simulation entity was still inside the suppression window."
                )
            if outcome == "Capacity reached":
                return (
                    f"Removed from investigation despite being eligible: {priority_text}, but "
                    "higher-priority alerts filled the per-step analyst capacity first."
                )
            return "Policy candidate without a final Sequential outcome."

        queue_frame["Decision reason"] = queue_frame.apply(
            queue_reason,
            axis=1,
        )

        queue_sort_columns = [
            column
            for column in ["step", "candidate_priority_rank", "rank_score"]
            if column in queue_frame.columns
        ]
        if queue_sort_columns:
            ascending_map = {
                "step": True,
                "candidate_priority_rank": True,
                "rank_score": False,
            }
            queue_frame = queue_frame.sort_values(
                queue_sort_columns,
                ascending=[
                    ascending_map[column]
                    for column in queue_sort_columns
                ],
                na_position="last",
            ).reset_index(drop=True)

        queue_frame["Priority"] = range(1, len(queue_frame) + 1)
        queue_frame["Transaction"] = (
            queue_frame["transaction_id"]
            .astype(str)
            .map(lambda value: f"TX-{value}")
        )
        queue_frame["Fraud risk"] = pd.to_numeric(
            queue_frame.get("fraud_score"),
            errors="coerce",
        )
        queue_frame["Fraud risk (%)"] = queue_frame["Fraud risk"] * 100.0
        queue_frame["Rank score"] = pd.to_numeric(
            queue_frame.get("rank_score"),
            errors="coerce",
        )

        # -----------------------------------------------------
        # FRAUD RISK BY TRANSACTION TYPE
        # -----------------------------------------------------
        st.markdown("### Fraud risk by transaction type")

        type_summary_records = selected_payload.get("transaction_type_summary", [])
        type_summary_frame = pd.DataFrame(type_summary_records)

        if type_summary_frame.empty:
            st.info(
                "Transaction-type summary is not available yet. Replace the simulation API "
                "with the updated queue API and restart FastAPI."
            )
        else:
            type_summary_frame = type_summary_frame.copy()
            type_summary_frame["Average model fraud risk (%)"] = (
                pd.to_numeric(
                    type_summary_frame["average_fraud_score"],
                    errors="coerce",
                ) * 100
            )
            type_summary_frame["Observed fraud rate (%)"] = (
                pd.to_numeric(
                    type_summary_frame["actual_fraud_rate"],
                    errors="coerce",
                ) * 100
            )

            type_summary_display = pd.DataFrame(
                {
                    "Transaction type": type_summary_frame["type"].astype(str),
                    "Transactions": type_summary_frame["transactions"].map(i),
                    "Average model fraud risk (%)": type_summary_frame[
                        "Average model fraud risk (%)"
                    ],
                    "Observed frauds": type_summary_frame["actual_frauds"].map(i),
                    "Observed fraud rate (%)": type_summary_frame[
                        "Observed fraud rate (%)"
                    ],
                    "Candidate alerts": type_summary_frame["candidate_alerts"].map(i),
                    "Investigated": type_summary_frame["investigated_alerts"].map(i),
                }
            ).sort_values(
                "Average model fraud risk (%)",
                ascending=False,
            )

            st.dataframe(
                type_summary_display,
                width="stretch",
                hide_index=True,
                column_config={
                    "Average model fraud risk (%)": st.column_config.NumberColumn(
                        format="%.2f%%",
                        help=(
                            "Mean fraud probability assigned by the model to transactions "
                            "of this type in the current replay."
                        ),
                    ),
                    "Observed fraud rate (%)": st.column_config.NumberColumn(
                        format="%.2f%%",
                        help=(
                            "Retrospective PaySim ground-truth fraud rate for this transaction "
                            "type. This value is for evaluation only and is not known at decision time."
                        ),
                    ),
                },
            )

            highest_model_type = type_summary_display.iloc[0]
            highest_actual_type = type_summary_display.sort_values(
                "Observed fraud rate (%)",
                ascending=False,
            ).iloc[0]

            st.caption(
                f"Highest average model fraud risk in the current replay: "
                f"{highest_model_type['Transaction type']} "
                f"({highest_model_type['Average model fraud risk (%)']:.2f}%). "
                f"Highest observed PaySim fraud rate: "
                f"{highest_actual_type['Transaction type']} "
                f"({highest_actual_type['Observed fraud rate (%)']:.2f}%). "
                "Model risk and observed fraud rate are different measures and should not be treated as identical."
            )

        # -----------------------------------------------------
        # PRIORITISED INVESTIGATION QUEUE — LAST SECTION
        # -----------------------------------------------------
        st.markdown("### Prioritised Investigation Queue")
        st.caption(
            "All transaction IDs and entity references in this queue are synthetic simulation "
            "identifiers from PaySim-based evaluation; no real customer or payment identifiers are displayed."
        )
        st.caption(
            "Transaction-level candidate queue. Priority is enforced separately within each "
            "operational step before the analyst-capacity decision is made."
        )

        outcome_filter = st.multiselect(
            "Queue outcome",
            ["Investigate", "Capacity reached", "Suppressed"],
            default=["Investigate", "Capacity reached", "Suppressed"],
            key=f"queue_outcome_{policy_choice}",
        )

        # Keep the complete filtered candidate queue. The table is scrollable so the
        # analyst can move past the investigated alerts and inspect lower-priority
        # candidates that were suppressed or rejected when capacity was exhausted.
        visible_queue = queue_frame[
            queue_frame["Outcome"].isin(outcome_filter)
        ].copy()

        display_queue = pd.DataFrame(
            {
                "Priority": visible_queue["Priority"],
                "Transaction": visible_queue["Transaction"],
                "Type": visible_queue.get("type"),
                "Step": visible_queue.get("step"),
                "Fraud risk (%)": visible_queue["Fraud risk (%)"],
                "Rank score": visible_queue["Rank score"],
                "Decision": visible_queue["Outcome"],
                "Reason": visible_queue["Decision reason"],
            }
        )

        investigated_in_view = int(
            (visible_queue["Outcome"] == "Investigate").sum()
        )
        not_investigated_in_view = int(
            visible_queue["Outcome"].isin(["Capacity reached", "Suppressed"]).sum()
        )

        st.caption(
            f"Showing the full filtered queue: {len(visible_queue):,} candidate alerts "
            f"({investigated_in_view:,} investigated; {not_investigated_in_view:,} not investigated). "
            "Scroll inside the table to inspect lower-priority alerts beyond the analyst-capacity cutoff."
        )

        st.dataframe(
            display_queue,
            width="stretch",
            height=560,
            hide_index=True,
            column_config={
                "Fraud risk (%)": st.column_config.NumberColumn(
                    "Fraud risk (%)",
                    format="%.1f%%",
                    help=(
                        "Probability assigned by the fraud model. 85% means the model estimates "
                        "an 85% probability of fraud."
                    ),
                ),
                "Rank score": st.column_config.NumberColumn(
                    "Rank score",
                    format="%.3f",
                    help=(
                        "Operational priority score used to order eligible alerts. It is not "
                        "a probability and should not be interpreted as a percentage."
                    ),
                ),
            },
        )

        with st.expander(
            "Fraud risk vs Rank score — difference and calculation",
            expanded=False,
        ):
            st.markdown(
                f"""
                **Fraud risk (%)** answers: *How likely does the ML model think this transaction is fraud?*  

                The trained model receives the transaction fields used at scoring time:
                `step`, `type`, `amount`, `oldbalanceOrg`, `newbalanceOrig`,
                `oldbalanceDest` and `newbalanceDest`. The trained preprocessing/model
                pipeline converts these inputs into a probability with `predict_proba`.
                A score of `0.85` is displayed here as **85% fraud risk**.

                **Rank score** answers: *How important is it to investigate this eligible alert relative to the others?*  

                Under the current `risk_zone` policy, the operational ranking function uses:
                **fraud risk + transaction amount + assumed investigation cost + false-negative factor**.
                The ranking logic therefore gives more weight to alerts where the potential
                fraud exposure is larger, rather than ranking by probability alone.

                The cost-aware components are:
                - **Expected fraud loss** = fraud probability × transaction amount × false-negative factor
                - **Expected investigation cost** = the estimated review-cost exposure under the current
                  investigation-cost assumption ({money(investigation_cost)} per review)
                - these values feed the cost-aware **Rank score**, which is used only to order alerts.

                **Important:** Rank score is **not** a probability and its absolute value is not interpreted
                as a percentage. Only its relative order matters: a larger value means higher operational priority.
                """
            )

        st.markdown("#### Alert Decision Explanation")
        transaction_options = visible_queue["Transaction"].tolist()

        if transaction_options:
            selected_transaction = st.selectbox(
                "Select a transaction to explain",
                transaction_options,
                key=f"decision_explanation_{policy_choice}",
            )
            selected_row = visible_queue.loc[
                visible_queue["Transaction"] == selected_transaction
            ].iloc[0]

            step_priority = selected_row.get("candidate_priority_rank")
            step_priority_text = (
                f"#{int(step_priority)} in step {i(selected_row.get('step'))}"
                if pd.notna(step_priority)
                else "Not available"
            )
            decision_tone = (
                "green"
                if selected_row["Outcome"] == "Investigate"
                else "orange"
                if selected_row["Outcome"] == "Suppressed"
                else "red"
            )

            detail_col1, detail_col2, detail_col3, detail_col4, detail_col5 = st.columns(5)
            with detail_col1:
                metric_card(
                    "Transaction type",
                    str(selected_row.get("type", "Unknown")),
                    "PaySim transaction category.",
                    "blue",
                )
            with detail_col2:
                metric_card(
                    "Fraud risk",
                    f"{n(selected_row.get('fraud_score')):.1%}",
                    "ML-estimated probability of fraud.",
                    "blue",
                )
            with detail_col3:
                metric_card(
                    "Rank score",
                    f"{n(selected_row.get('rank_score')):,.3f}",
                    "Operational priority; not a probability.",
                    "blue",
                )
            with detail_col4:
                metric_card(
                    "Priority in step",
                    step_priority_text,
                    "Order used when capacity is applied.",
                    "blue",
                )
            with detail_col5:
                metric_card(
                    "Final decision",
                    str(selected_row["Outcome"]),
                    "Sequential operational outcome.",
                    decision_tone,
                )

            st.markdown(
                f"""
                <div class="decision-box">
                    <strong>Why this decision?</strong><br>
                    {html.escape(str(selected_row['Decision reason']))}
                    <br><br>
                    <span class="small">
                    Evaluation label: <strong>{"Confirmed fraud" if i(selected_row.get('isFraud')) == 1 else "Non-fraud transaction"}</strong>.
                    This label is available only for retrospective PaySim evaluation and is not used by the analyst at decision time.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("Technical details", expanded=False):
        st.json(
            {
                "selected_policy": policy_choice,
                "candidate_alerts": candidates,
                "suppressed_alerts": suppressed,
                "eligible_after_suppression": eligible_after_suppression,
                "capacity_per_step": int(alert_budget_per_step),
                "unique_steps": unique_steps,
                "maximum_sequential_capacity": maximum_capacity,
                "investigated_alerts": accepted,
                "capacity_rejected": rejected,
            }
        )


# =========================================================
# 4. SEQUENTIAL WORKFLOW
# =========================================================

with workflow_tab:
    st.header("Sequential Workflow")
    st.caption(
        "Offline chronological replay that imitates successive decision cycles; "
        "this is not a deployed real-time transaction stream."
    )

    unique_steps = i(parameters.get("unique_steps"))



    # Process first, as requested.
    st.markdown("### Seven-step decision process")

    compact_steps = [
        ("1. Transactions arrive", "Historical transactions are replayed chronologically."),
        ("2. Fraud risk is calculated", "The fixed ML model assigns a fraud-risk score."),
        ("3. Candidate alerts are created", "Static or Adaptive policy selects cases."),
        ("4. Repeated alerts may be suppressed", "Duplicate entity alerts may be filtered."),
        ("5. Alerts are prioritised", "Higher-priority cases are considered first."),
        ("6. Analyst capacity is applied", "Only alerts within each step limit enter the queue."),
        ("7. Outcomes are evaluated", "Investigated alerts are compared with fraud labels."),
    ]

    for index, (title, explanation) in enumerate(compact_steps):
        workflow_step(title, explanation)
        if index < len(compact_steps) - 1:
            arrow()

    st.markdown(
        f"""
        <div class="takeaway">
            <strong>Key interpretation</strong><br>
            The selected replay contains <strong>{unique_steps}</strong> chronological
            PaySim steps. Ranking, suppression and the limit of
            <strong>{int(alert_budget_per_step)}</strong> alerts are applied separately
            within each step.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Methodological context: Batch vs Sequential", expanded=False):
        st.markdown(
            """
            **Why is this important?**  
            Sequential replay introduces operational constraints that are absent from a simple
            Batch evaluation. Batch is retained as an ideal methodological baseline; the main
            operational conclusions of the dashboard are based on the Sequential replay.
            """
        )

        batch_vs_sequential = pd.DataFrame(
            [
                {
                    "Feature": "Transaction handling",
                    "Batch evaluation": "All evaluated transactions considered globally",
                    "Sequential simulation": "Transactions replayed chronologically",
                },
                {
                    "Feature": "Analyst capacity",
                    "Batch evaluation": "Not applied to the global policy result",
                    "Sequential simulation": "Applied separately in every operational step",
                },
                {
                    "Feature": "Suppression",
                    "Batch evaluation": "Not part of the ideal policy comparison",
                    "Sequential simulation": "Repeated alerts may be filtered",
                },
                {
                    "Feature": "Question answered",
                    "Batch evaluation": "What could the policy detect?",
                    "Sequential simulation": "What can the operation actually investigate?",
                },
            ]
        )

        st.dataframe(batch_vs_sequential, width="stretch", hide_index=True)

        st.caption(
            "The machine-learning model itself is unchanged. The difference comes from "
            "the operational constraints introduced around the model."
        )

    st.markdown("### Is this truly real time?")

    realtime_table = pd.DataFrame(
        [
            {
                "Feature": "Data source",
                "Current simulation": "Historical stored transactions",
                "True real-time system": "Continuously arriving live transactions",
            },
            {
                "Feature": "Processing",
                "Current simulation": "Offline chronological replay",
                "True real-time system": "Immediate event-by-event processing",
            },
            {
                "Feature": "Alerts",
                "Current simulation": "Simulated analyst queue",
                "True real-time system": "Production alerts sent immediately",
            },
            {
                "Feature": "Correct description",
                "Current simulation": "Sequential / real-time-oriented simulation",
                "True real-time system": "Live real-time fraud operations",
            },
        ]
    )

    st.dataframe(
        realtime_table,
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        """
        <div class="warning">
            <strong>Correct terminology</strong><br>
            This is not a deployed real-time system. It is an offline sequential
            simulation or chronological replay that imitates real-time decision cycles.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="decision-box">
            <strong>Management recommendation</strong><br>
            Before production use, define how one operational step maps to real time,
            connect the system to a live transaction stream and collect delayed analyst
            outcomes for continuous monitoring.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Technical details"):
        st.markdown("#### PaySim step")
        st.markdown(
            f"""
            **Meaning in this implementation**  
            `step` is the chronological grouping variable used by the replay. Transactions
            with the same step value are treated as one operational decision cycle. The
            dashboard does not convert a step into a fixed real-world duration.

            **Role in this dashboard**  
            Transactions are processed in step order. Within each of the
            **{unique_steps} operational steps** in the selected replay, candidate alerts
            are ranked, repeat-alert suppression is applied and the analyst limit of
            **{int(alert_budget_per_step)} alerts per step** is enforced independently.
            When the replay moves to the next step, the analyst limit is reset. Unused
            capacity from an earlier step is not transferred to a later one.

            **Important distinction**  
            An operational step is not a Monitoring Window. A step controls the sequential
            decision logic and analyst-capacity reset. A Monitoring Window is only a reporting
            block of consecutive transactions used to display trends.
            """
        )

        st.divider()
        st.json(
            {
                "simulation_type": "offline chronological replay",
                "capacity_per_step": int(alert_budget_per_step),
                "suppression_window": int(suppression_window),
                "unique_steps": i(parameters.get("unique_steps")),
            }
        )


# =========================================================
# 5. MONITORING
# =========================================================

with monitoring_tab:
    st.header("Monitoring")

    monitoring_window_size = int(
        params.get("monitoring_window_size", 1000)
    )
    monitoring_window_count = len(adaptive_windows)

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Monitoring windows</strong><br>
            For reporting, the replay is divided into
            <strong>{monitoring_window_count}</strong> consecutive windows of
            <strong>{monitoring_window_size:,} transactions</strong>.
            They show how workload and performance change during the replay.<br><br>
            <span class="small"><strong>Do not confuse these with operational steps:</strong>
            an operational step is one chronological decision cycle where analyst capacity
            is enforced and reset. A Monitoring Window is only a reporting group used to make
            trends easier to inspect.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if adaptive_windows.empty:
        st.info("No monitoring-window data are available.")
    else:
        preferred_columns = [
            "window",
            "candidate_alerts",
            "accepted_alerts",
            "capacity_rejected",
            "frauds_missed",
            "recall",
            "operational_cost",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in adaptive_windows.columns
        ]

        monitoring_display = adaptive_windows[
            available_columns
        ].copy()

        if "recall" in monitoring_display.columns:
            monitoring_display["recall"] = (
                monitoring_display["recall"].map(pct)
            )

        if "operational_cost" in monitoring_display.columns:
            monitoring_display["operational_cost"] = (
                monitoring_display["operational_cost"].map(money)
            )

        monitoring_display = monitoring_display.rename(
            columns={
                "window": "Monitoring window",
                "candidate_alerts": "Candidate alerts",
                "accepted_alerts": "Investigated alerts",
                "capacity_rejected": "Budget overflow",
                "frauds_missed": "Frauds missed",
                "recall": "Recall",
                "operational_cost": "Estimated operational cost (€)",
            }
        )

        st.markdown("### Results by monitoring window")
        st.dataframe(
            monitoring_display,
            width="stretch",
            hide_index=True,
        )

        st.markdown(
            """
            <div class="takeaway">
                <strong>How to read the table</strong><br>
                Each row is one consecutive transaction window. Compare rows to identify
                workload peaks, missed fraud and changes in estimated operational cost.
            </div>
            """,
            unsafe_allow_html=True,
        )


        def render_monitoring_chart(
            column: str,
            title: str,
            y_axis_label: str,
            value_formatter,
            interpretation: str,
        ) -> None:
            if not {"window", column}.issubset(adaptive_windows.columns):
                return

            chart_frame = adaptive_windows[
                ["window", column]
            ].copy()

            chart_frame[column] = pd.to_numeric(
                chart_frame[column],
                errors="coerce",
            )
            chart_frame = chart_frame.dropna()

            if chart_frame.empty:
                return

            highest_row = chart_frame.loc[
                chart_frame[column].idxmax()
            ]
            lowest_row = chart_frame.loc[
                chart_frame[column].idxmin()
            ]

            highest_window = i(highest_row["window"])
            lowest_window = i(lowest_row["window"])
            highest_value = float(highest_row[column])
            lowest_value = float(lowest_row[column])
            average_value = float(chart_frame[column].mean())
            trend = trend_label(chart_frame[column])

            chart_col, observations_col = st.columns([2.15, 1])

            with chart_col:
                dashboard_bg = "#0e1117"
                dashboard_text = "#fafafa"
                dashboard_grid = "#4a5568"
                dashboard_blue = "#2d8cff"

                fig, ax = plt.subplots(figsize=(8.2, 4.2))
                fig.patch.set_facecolor(dashboard_bg)
                ax.set_facecolor(dashboard_bg)

                ax.plot(
                    chart_frame["window"],
                    chart_frame[column],
                    marker="o",
                    color=dashboard_blue,
                    linewidth=2.2,
                    markersize=6,
                )
                ax.set_title(title, color=dashboard_text, pad=12)
                ax.set_xlabel("Monitoring Window", color=dashboard_text)
                ax.set_ylabel(y_axis_label, color=dashboard_text)
                ax.tick_params(axis="both", colors=dashboard_text)
                ax.grid(True, color=dashboard_grid, alpha=0.35)

                for spine in ax.spines.values():
                    spine.set_color(dashboard_grid)

                fig.tight_layout()

                st.pyplot(
                    fig,
                    width="stretch",
                    transparent=False,
                )
                plt.close(fig)

                st.markdown(
                    f"""
                    <div class="chart-conclusion">
                        <strong>Conclusion</strong><br>
                        {html.escape(interpretation)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with observations_col:
                st.markdown(
                    f"""
                    <div class="takeaway">
                        <strong>Key observations</strong><br><br>
                        <strong>Highest value</strong><br>
                        Monitoring Window {highest_window}<br>
                        {html.escape(value_formatter(highest_value))}
                        <br><br>
                        <strong>Lowest value</strong><br>
                        Monitoring Window {lowest_window}<br>
                        {html.escape(value_formatter(lowest_value))}
                        <br><br>
                        <strong>Average</strong><br>
                        {html.escape(value_formatter(average_value))}
                        <br><br>
                        <strong>Overall pattern</strong><br>
                        {html.escape(trend)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div class="chart-spacer"></div>',
                unsafe_allow_html=True,
            )

        render_monitoring_chart(
            column="candidate_alerts",
            title="Candidate Alerts per Monitoring Window",
            y_axis_label="Candidate Alerts",
            value_formatter=lambda value: f"{value:,.0f} alerts",
            interpretation=(
                "This chart shows how many transactions were proposed as alerts "
                "in each period. Large differences between windows indicate that "
                "the incoming alert workload was not evenly distributed."
            ),
        )

        render_monitoring_chart(
            column="accepted_alerts",
            title="Investigated Alerts per Monitoring Window",
            y_axis_label="Investigated Alerts",
            value_formatter=lambda value: f"{value:,.0f} alerts",
            interpretation=(
                "This chart shows the workload that actually reached analysts. "
                "Values close to the available window capacity indicate periods "
                "where the investigation team was heavily utilised."
            ),
        )

        render_monitoring_chart(
             column="capacity_rejected",
             title="Budget Overflow Alerts per Monitoring Window",
             y_axis_label="Budget Overflow Alerts",
             value_formatter=lambda value: f"{value:,.0f} alerts",
             interpretation=(
                "These alerts were not investigated because the available analyst "
                "budget for that operational step had already been reached. "
                "Higher values indicate periods where more candidate alerts "
                "competed for the available investigation capacity."
          ),
        )

        render_monitoring_chart(
            column="frauds_missed",
            title="Missed Frauds per Monitoring Window",
            y_axis_label="Missed Frauds",
            value_formatter=lambda value: f"{value:,.0f} fraud cases",
            interpretation=(
                "This chart identifies when the largest number of real fraud cases "
                "escaped investigation. Peaks indicate periods where the policy, "
                "ranking or available capacity was least effective."
            ),
        )

        render_monitoring_chart(
            column="operational_cost",
            title="Estimated Operational Cost per Monitoring Window",
            y_axis_label="Estimated Operational Cost (€)",
            value_formatter=lambda value: f"€{value:,.2f}",
            interpretation=(
                "This chart combines investigation workload with the cost assigned "
                "to missed fraud. Cost peaks reveal the periods with the greatest "
                "overall operational impact."
            ),
        )

        # Concise monitoring interpretation.
        candidate_peak_text = "not available"
        cost_peak_text = "not available"

        if "candidate_alerts" in adaptive_windows.columns:
            row = adaptive_windows.loc[adaptive_windows["candidate_alerts"].idxmax()]
            candidate_peak_text = (
                f"Window {i(row['window'])} "
                f"({i(row['candidate_alerts']):,} candidate alerts)"
            )

        if "operational_cost" in adaptive_windows.columns:
            row = adaptive_windows.loc[adaptive_windows["operational_cost"].idxmax()]
            cost_peak_text = (
                f"Window {i(row['window'])} "
                f"({money(row['operational_cost'])})"
            )

        # More specific interpretation tied directly to the monitoring table.
        st.markdown(
            f"""
<div class="decision-box">
<strong>What does the monitoring reveal?</strong><br><br>
<strong>1. Some periods create much more pressure on analysts.</strong> Monitoring Window 1 has the highest candidate-alert volume (<strong>159</strong>) and the largest budget overflow (<strong>133 rejected alerts</strong>). This means that, during this period, the number of suspicious transactions substantially exceeded the available investigation capacity.<br><br>
<strong>2. More alerts do not necessarily mean higher operational cost.</strong> Although Window 1 has the highest workload, the <strong>Estimated operational cost (€)</strong> column peaks in Monitoring Window 2 at <strong>€609,383.96</strong>. This is because the cost is driven mainly by the value of fraud that was missed, rather than simply by the number of alerts generated.<br><br>
<strong>3. Investigating more alerts does not automatically guarantee better fraud detection.</strong> For example, Monitoring Window 6 investigated <strong>47 alerts</strong> but achieved <strong>33.3% recall</strong> and missed <strong>8 frauds</strong>, whereas Window 5 investigated <strong>92 alerts</strong> and achieved <strong>93.8% recall</strong>. This suggests that performance depends not only on how many alerts analysts can investigate, but also on whether the system prioritises the right alerts for investigation.
</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
<div class="info-box">
<strong>Monitoring implication</strong><br>
Overall results can hide periods in which the system is under operational pressure. Monitoring performance over time helps identify when analyst capacity becomes insufficient and whether alert prioritisation is still directing limited resources toward the most valuable investigations.
</div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Technical details"):
        st.caption(
            "In this dashboard, a step is a chronological decision cycle used by "
            "the sequential replay. It does not represent a fixed real-world duration. "
            "The selected replay contains the step values present in the evaluated transactions."
        )
        st.json(
            {
                "transactions_evaluated": int(transaction_limit),
                "paysim_steps_in_replay": i(parameters.get("unique_steps")),
                "monitoring_window_size": monitoring_window_size,
                "monitoring_windows": monitoring_window_count,
                "monitoring_mode": "offline chronological observation",
            }
        )

# =========================================================
# 6. SENSITIVITY ANALYSIS
# =========================================================

with sensitivity_tab:
    st.header("Sensitivity Analysis")

    st.markdown(
        """
        <div class="info-box">
            <strong>What is being tested?</strong><br>
            This section checks whether the decision system behaves in a clear and
            predictable way when one operating setting changes. Each experiment changes
            <strong>one parameter at a time</strong>; every other setting remains fixed.
            The purpose is to understand which settings matter most and whether the
            Adaptive policy remains useful under different operating conditions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    experiment_definitions = {
        "Transaction volume": {
            "parameter": "limit",
            "values": (1000.0, 3000.0, 10000.0),
            "display_values": "1,000 · 3,000 · 10,000 transactions",
            "purpose": "Tests how the system behaves as the transaction workload grows while analyst resources remain fixed.",
        },
        "Analyst capacity": {
            "parameter": "alert_budget_per_step",
            "values": (10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0),
            "display_values": "10–100 alerts per operational step",
            "purpose": "Tests whether additional analyst resources reduce overflow and improve fraud coverage.",
        },
        "Investigation cost": {
            "parameter": "investigation_cost",
            "values": (5.0, 10.0, 15.0, 20.0, 25.0),
            "display_values": "€5 · €10 · €15 · €20 · €25 per investigation",
            "purpose": "Tests whether the economic comparison changes when reviewing one alert becomes more expensive.",
        },
        "Suppression window": {
            "parameter": "suppression_window",
            "values": (0.0, 1.0, 2.0, 3.0, 5.0),
            "display_values": "0 · 1 · 2 · 3 · 5 steps",
            "purpose": "Tests how strongly repeated alerts are filtered before analysts review them.",
        },
        "Adaptive budget multiplier": {
            "parameter": "budget_multiplier",
            "values": (1.0, 1.2, 1.3, 1.4, 1.6, 1.8, 2.0),
            "display_values": "1.0–2.0",
            "purpose": "Tests how broadly the Adaptive policy expands its candidate-alert selection.",
        },
        "Static threshold": {
            "parameter": "static_threshold",
            "values": (0.30, 0.40, 0.50, 0.60, 0.70),
            "display_values": "0.30 · 0.40 · 0.50 · 0.60 · 0.70",
            "purpose": "Tests how dependent the Static baseline is on its fixed fraud-score cut-off.",
        },
        "Minimum Adaptive threshold": {
            "parameter": "risk_zone_floor",
            "values": (0.10, 0.20, 0.30, 0.40, 0.50),
            "display_values": "0.10 · 0.20 · 0.30 · 0.40 · 0.50",
            "purpose": (
                "Sets the minimum fraud score a transaction must have before it can be considered "
                "by the Adaptive policy. Lower values allow more transactions to be considered; "
                "higher values make selection more restrictive."
            ),
        },
    }

    experiment_names = list(experiment_definitions)

    with st.expander(
        "What experiments are included?",
        expanded=False,
    ):
        st.caption(
            "Open this section when you want the methodological detail. "
            "Each experiment changes one parameter while the others remain fixed."
        )

        for start in range(0, len(experiment_names), 2):
            row_names = experiment_names[start:start + 2]
            columns = st.columns(2)
            for column, experiment_name in zip(columns, row_names):
                definition = experiment_definitions[experiment_name]
                with column:
                    st.markdown(
                        f"""
                        <div class="definition-card">
                            <strong>{html.escape(experiment_name)}</strong>
                            <p><strong>Values tested:</strong><br>{html.escape(definition['display_values'])}</p>
                            <div class="small"><strong>Purpose:</strong> {html.escape(definition['purpose'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.caption(
            "The experiments are executed through one optimized API request. "
            "The backend reuses scored data and repeated calculations, and completed results are cached."
        )

    run_sensitivity = st.button(
        "Run all sensitivity experiments",
        type="primary",
        width="stretch",
    )

    if run_sensitivity:
        try:
            with st.spinner(
                "Running seven one-at-a-time experiments through the optimized sensitivity endpoint..."
            ):
                sensitivity_payload = load_sensitivity_data(
                    dict(params),
                    cache_schema_version="operational-flow-v2",
                )
                results = prepare_sensitivity_results(sensitivity_payload)

            missing_experiments = [
                name for name in experiment_names if name not in results
            ]
            if missing_experiments:
                raise ValueError(
                    "The sensitivity endpoint did not return results for: "
                    + ", ".join(missing_experiments)
                )

            st.session_state["final_sensitivity_results"] = {
                "results": results,
                "base_params": dict(params),
                "execution_metadata": sensitivity_payload.get(
                    "execution_metadata", {}
                ),
            }
            st.success(
                "Sensitivity experiments completed through one API request."
            )
        except requests.exceptions.Timeout:
            st.error(
                "The optimized sensitivity request timed out. Try a smaller baseline "
                "transaction volume or check the FastAPI terminal."
            )
        except requests.exceptions.RequestException as exc:
            st.error(
                "The sensitivity endpoint could not complete the experiments."
            )
            st.exception(exc)
        except Exception as exc:
            st.error("The sensitivity analysis could not be completed.")
            st.exception(exc)

    saved_analysis = st.session_state.get("final_sensitivity_results")

    if not saved_analysis:
        st.markdown(
            """
            <div class="compact-note" style="border-left:4px solid #1976d2;background:rgba(25,118,210,.07);">
                Run the experiments to generate real results. The conclusions below are not
                pre-filled or hardcoded; they are created from the API output.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        if saved_analysis.get("base_params") != params:
            st.warning(
                "These results were generated with earlier sidebar settings. Run the "
                "experiments again to align them with the current scenario."
            )

        result_map = saved_analysis["results"]

        missing_flow_metrics = any(
            row.get("adaptive_candidates") is None
            or row.get("adaptive_overflow") is None
            for rows in result_map.values()
            for row in rows
        )
        if missing_flow_metrics:
            st.warning(
                "Operational sensitivity metrics are missing from the API response. "
                "Restart FastAPI with the updated simulation API, then press "
                "'Run / refresh sensitivity experiments'. Missing values are shown as N/A, "
                "not as zero."
            )

        # -----------------------------------------------------
        # DECISION SCENARIO EXPLORER
        # -----------------------------------------------------
        st.markdown("### Decision Scenario Explorer")
        st.markdown(
            """
            <div class="info-box">
                <strong>Decision question</strong><br>
                How would changing one operational decision parameter affect fraud coverage,
                workload and estimated cost? Choose a scenario below. Each comparison uses
                already-tested sensitivity results and changes only one parameter at a time.
            </div>
            """,
            unsafe_allow_html=True,
        )

        scenario_choice = st.radio(
            "Scenario to explore",
            ["Analyst capacity", "Adaptive budget multiplier"],
            horizontal=True,
            key="decision_scenario_choice",
        )

        if scenario_choice == "Analyst capacity":
            scenario_df = pd.DataFrame(result_map.get("Analyst capacity", []))

            if scenario_df.empty:
                st.info(
                    "Run the Analyst capacity sensitivity experiment to enable this scenario."
                )
            else:
                scenario_df = scenario_df.sort_values("value").reset_index(drop=True)
                scenario_values = [int(round(n(value))) for value in scenario_df["value"]]
                baseline_value = int(alert_budget_per_step)

                current_index = min(
                    range(len(scenario_values)),
                    key=lambda index: abs(scenario_values[index] - baseline_value),
                )
                alternative_index = min(current_index + 1, len(scenario_values) - 1)

                c1, c2, c3 = st.columns(3)
                with c1:
                    whatif_policy = st.radio(
                        "Policy to compare",
                        ["Adaptive", "Static"],
                        horizontal=True,
                        key="capacity_whatif_policy",
                    )
                with c2:
                    current_choice = st.selectbox(
                        "Current capacity",
                        scenario_values,
                        index=current_index,
                        key="capacity_current",
                    )
                with c3:
                    alternative_choice = st.selectbox(
                        "Alternative capacity",
                        scenario_values,
                        index=alternative_index,
                        key="capacity_alternative",
                    )

                current_row = scenario_df.loc[
                    scenario_df["value"].round().astype(int) == int(current_choice)
                ].iloc[0]
                alternative_row = scenario_df.loc[
                    scenario_df["value"].round().astype(int) == int(alternative_choice)
                ].iloc[0]

                prefix = "adaptive" if whatif_policy == "Adaptive" else "static"
                metrics_to_compare = [
                    ("Candidate alerts", f"{prefix}_candidates", "count"),
                    ("Investigated alerts", f"{prefix}_investigated", "count"),
                    ("Frauds detected", f"{prefix}_detected", "count"),
                    ("Recall", f"{prefix}_recall", "pct"),
                    ("Estimated operational cost", f"{prefix}_cost", "money"),
                    ("Suppressed alerts", f"{prefix}_suppressed", "count"),
                    ("Capacity-rejected alerts", f"{prefix}_overflow", "count"),
                ]

                records = []
                for label, column, metric_type in metrics_to_compare:
                    current_value = n(current_row.get(column))
                    alternative_value = n(alternative_row.get(column))
                    difference = alternative_value - current_value

                    if metric_type == "pct":
                        current_display = pct(current_value)
                        alternative_display = pct(alternative_value)
                        change_display = f"{difference * 100:+.1f} pp"
                    elif metric_type == "money":
                        current_display = money(current_value)
                        alternative_display = money(alternative_value)
                        if difference < -0.01:
                            change_display = f"{money(abs(difference))} lower"
                        elif difference > 0.01:
                            change_display = f"{money(difference)} higher"
                        else:
                            change_display = "No change"
                    else:
                        raw_current = current_row.get(column)
                        raw_alternative = alternative_row.get(column)
                        if (
                            raw_current is None
                            or raw_alternative is None
                            or pd.isna(raw_current)
                            or pd.isna(raw_alternative)
                        ):
                            current_display = "N/A"
                            alternative_display = "N/A"
                            change_display = "N/A"
                        else:
                            current_display = f"{int(round(current_value)):,}"
                            alternative_display = f"{int(round(alternative_value)):,}"
                            change_display = f"{int(round(difference)):+,}"

                    records.append(
                        {
                            "Outcome": label,
                            f"Current ({int(current_choice)}/step)": current_display,
                            f"Alternative ({int(alternative_choice)}/step)": alternative_display,
                            "Change": change_display,
                        }
                    )

                st.dataframe(pd.DataFrame(records), width="stretch", hide_index=True)

                recall_change = (
                    n(alternative_row.get(f"{prefix}_recall"))
                    - n(current_row.get(f"{prefix}_recall"))
                )
                cost_change = (
                    n(alternative_row.get(f"{prefix}_cost"))
                    - n(current_row.get(f"{prefix}_cost"))
                )
                current_overflow = optional_i(
                    current_row.get(f"{prefix}_overflow")
                )
                alternative_overflow = optional_i(
                    alternative_row.get(f"{prefix}_overflow")
                )
                overflow_change = (
                    alternative_overflow - current_overflow
                    if current_overflow is not None and alternative_overflow is not None
                    else None
                )

                parts = []
                if recall_change > 1e-9:
                    parts.append(
                        f"recall improves by {recall_change * 100:.1f} percentage points"
                    )
                elif recall_change < -1e-9:
                    parts.append(
                        f"recall decreases by {abs(recall_change) * 100:.1f} percentage points"
                    )
                else:
                    parts.append("recall is unchanged")

                if cost_change < -0.01:
                    parts.append(
                        f"estimated operational cost falls by {money(abs(cost_change))}"
                    )
                elif cost_change > 0.01:
                    parts.append(
                        f"estimated operational cost rises by {money(cost_change)}"
                    )
                else:
                    parts.append("estimated operational cost is unchanged")

                if overflow_change is not None:
                    if overflow_change < 0:
                        parts.append(
                            f"capacity overflow falls by {abs(overflow_change):,} alerts"
                        )
                    elif overflow_change > 0:
                        parts.append(
                            f"capacity overflow rises by {overflow_change:,} alerts"
                        )

                st.markdown(
                    f"""
                    <div class="takeaway">
                        <strong>Decision implication</strong><br>
                        Changing capacity from <strong>{int(current_choice)}</strong> to
                        <strong>{int(alternative_choice)}</strong> alerts per step means
                        {html.escape("; ".join(parts))}.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            scenario_df = pd.DataFrame(
                result_map.get("Adaptive budget multiplier", [])
            )

            if scenario_df.empty:
                st.info(
                    "Run the Adaptive budget multiplier sensitivity experiment to enable this scenario."
                )
            else:
                scenario_df = scenario_df.sort_values("value").reset_index(drop=True)
                scenario_values = [round(n(value), 1) for value in scenario_df["value"]]
                baseline_value = round(float(budget_multiplier), 1)

                current_index = min(
                    range(len(scenario_values)),
                    key=lambda index: abs(scenario_values[index] - baseline_value),
                )
                alternative_index = min(current_index + 1, len(scenario_values) - 1)

                c1, c2 = st.columns(2)
                with c1:
                    current_choice = st.selectbox(
                        "Current multiplier",
                        scenario_values,
                        index=current_index,
                        key="multiplier_current",
                    )
                with c2:
                    alternative_choice = st.selectbox(
                        "Alternative multiplier",
                        scenario_values,
                        index=alternative_index,
                        key="multiplier_alternative",
                    )

                current_row = scenario_df.loc[
                    scenario_df["value"].round(1) == round(float(current_choice), 1)
                ].iloc[0]
                alternative_row = scenario_df.loc[
                    scenario_df["value"].round(1) == round(float(alternative_choice), 1)
                ].iloc[0]

                metrics_to_compare = [
                    ("Candidate alerts", "adaptive_candidates", "count"),
                    ("Investigated alerts", "adaptive_investigated", "count"),
                    ("Frauds detected", "adaptive_detected", "count"),
                    ("Recall", "adaptive_recall", "pct"),
                    ("Estimated operational cost", "adaptive_cost", "money"),
                    ("Capacity-rejected alerts", "adaptive_overflow", "count"),
                ]

                records = []
                for label, column, metric_type in metrics_to_compare:
                    current_value = n(current_row.get(column))
                    alternative_value = n(alternative_row.get(column))
                    difference = alternative_value - current_value

                    if metric_type == "pct":
                        current_display = pct(current_value)
                        alternative_display = pct(alternative_value)
                        change_display = f"{difference * 100:+.1f} pp"
                    elif metric_type == "money":
                        current_display = money(current_value)
                        alternative_display = money(alternative_value)
                        if difference < -0.01:
                            change_display = f"{money(abs(difference))} lower"
                        elif difference > 0.01:
                            change_display = f"{money(difference)} higher"
                        else:
                            change_display = "No change"
                    else:
                        raw_current = current_row.get(column)
                        raw_alternative = alternative_row.get(column)
                        if (
                            raw_current is None
                            or raw_alternative is None
                            or pd.isna(raw_current)
                            or pd.isna(raw_alternative)
                        ):
                            current_display = "N/A"
                            alternative_display = "N/A"
                            change_display = "N/A"
                        else:
                            current_display = f"{int(round(current_value)):,}"
                            alternative_display = f"{int(round(alternative_value)):,}"
                            change_display = f"{int(round(difference)):+,}"

                    records.append(
                        {
                            "Outcome": label,
                            f"Current (x{float(current_choice):.1f})": current_display,
                            f"Alternative (x{float(alternative_choice):.1f})": alternative_display,
                            "Change": change_display,
                        }
                    )

                st.dataframe(pd.DataFrame(records), width="stretch", hide_index=True)

                st.caption(
                    "The Adaptive budget multiplier controls the size of the Adaptive candidate-alert "
                    "budget relative to the Static baseline alert volume. For example, x1.4 permits an "
                    "Adaptive budget equal to approximately 140% of the Static alert count before the "
                    "Sequential analyst-capacity constraint is applied."
                )

                recall_change = (
                    n(alternative_row.get("adaptive_recall"))
                    - n(current_row.get("adaptive_recall"))
                )
                candidate_change = (
                    i(alternative_row.get("adaptive_candidates"))
                    - i(current_row.get("adaptive_candidates"))
                )
                cost_change = (
                    n(alternative_row.get("adaptive_cost"))
                    - n(current_row.get("adaptive_cost"))
                )

                if recall_change > 1e-9 and cost_change <= 0.01:
                    implication = (
                        f"The broader Adaptive budget adds {candidate_change:+,} candidate alerts, "
                        f"improves recall by {recall_change * 100:.1f} percentage points and does "
                        "not increase estimated operational cost."
                    )
                elif recall_change > 1e-9:
                    implication = (
                        f"The broader Adaptive budget adds {candidate_change:+,} candidate alerts "
                        f"and improves recall by {recall_change * 100:.1f} percentage points, "
                        f"but estimated operational cost increases by {money(max(cost_change, 0))}."
                    )
                elif candidate_change > 0:
                    implication = (
                        f"The broader Adaptive budget adds {candidate_change:+,} candidate alerts "
                        "without improving recall in this tested scenario, suggesting diminishing returns."
                    )
                else:
                    implication = (
                        "The two tested multiplier settings produce little operational difference "
                        "under the current configuration."
                    )

                st.markdown(
                    f"""
                    <div class="takeaway">
                        <strong>Decision implication</strong><br>
                        {html.escape(implication)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        def build_plain_finding(frame: pd.DataFrame) -> str:
            adaptive_wins = int((frame["winner"] == "Adaptive").sum())
            static_wins = int((frame["winner"] == "Static").sum())
            ties = int((frame["winner"] == "Tie").sum())
            total = len(frame)
            if adaptive_wins > static_wins:
                return f"Adaptive was preferable in {adaptive_wins} of {total} tested settings; Static won {static_wins}, with {ties} ties."
            if static_wins > adaptive_wins:
                return f"Static was preferable in {static_wins} of {total} tested settings; Adaptive won {adaptive_wins}, with {ties} ties."
            return f"Neither policy dominated: each won {adaptive_wins} settings, with {ties} ties."

        # Build a concise, data-driven overview before the detailed results.
        overview_frames: dict[str, pd.DataFrame] = {
            experiment_name: pd.DataFrame(result_map[experiment_name])
            for experiment_name in experiment_names
        }

        overview_family_winners: list[str] = []
        for experiment_name in experiment_names:
            overview_frame = overview_frames[experiment_name]
            overview_counts = overview_frame["winner"].value_counts()
            overview_adaptive = int(overview_counts.get("Adaptive", 0))
            overview_static = int(overview_counts.get("Static", 0))
            if overview_adaptive > overview_static:
                overview_family_winners.append("Adaptive")
            elif overview_static > overview_adaptive:
                overview_family_winners.append("Static")
            else:
                overview_family_winners.append("Tie")

        overview_adaptive_families = overview_family_winners.count("Adaptive")
        overview_static_families = overview_family_winners.count("Static")
        overview_tied_families = overview_family_winners.count("Tie")

        adaptive_best_experiments = [
            name for name, winner in zip(experiment_names, overview_family_winners)
            if winner == "Adaptive"
        ]
        static_best_experiments = [
            name for name, winner in zip(experiment_names, overview_family_winners)
            if winner == "Static"
        ]
        tied_experiments = [
            name for name, winner in zip(experiment_names, overview_family_winners)
            if winner == "Tie"
        ]

        adaptive_best_text = " · ".join(adaptive_best_experiments) or "None"
        static_best_text = " · ".join(static_best_experiments) or "None"
        tied_text = " · ".join(tied_experiments) or "None"

        largest_gap_experiment = "Not available"
        largest_gap_value = 0.0
        largest_gap_setting: float | None = None
        for experiment_name, overview_frame in overview_frames.items():
            if overview_frame.empty or "recall_difference" not in overview_frame.columns:
                continue
            absolute_gap = pd.to_numeric(
                overview_frame["recall_difference"], errors="coerce"
            ).abs()
            if absolute_gap.dropna().empty:
                continue
            row_index = absolute_gap.idxmax()
            current_gap = float(absolute_gap.loc[row_index])
            if current_gap > largest_gap_value:
                largest_gap_value = current_gap
                largest_gap_experiment = experiment_name
                largest_gap_setting = n(overview_frame.loc[row_index, "value"])

        if overview_adaptive_families > overview_static_families:
            overall_direction = (
                "Adaptive produced the stronger overall pattern across the tested "
                "parameter families, although it was not superior in every setting."
            )
        elif overview_static_families > overview_adaptive_families:
            overall_direction = (
                "Static produced the stronger overall pattern across the tested "
                "parameter families, so Adaptive superiority is not supported universally."
            )
        else:
            overall_direction = (
                "Neither policy dominated across the tested parameter families; "
                "the preferred choice depends on the operating configuration."
            )

        gap_detail = (
            f"{largest_gap_experiment} at tested value {largest_gap_setting:g}, "
            f"where the absolute recall difference reached {largest_gap_value:.2%}."
            if largest_gap_setting is not None
            else "No measurable recall separation was available."
        )

        baseline_params = saved_analysis.get("base_params", params)

        st.markdown("### Controlled experimental design")
        st.markdown(
            """
            <div class="question-card">
                To make each comparison fair, every experiment changed only the parameter
                named in that experiment. The remaining settings stayed at the baseline
                values shown below. For example, during the Analyst capacity experiment,
                analyst capacity changed while transaction volume, thresholds, costs,
                suppression and the Adaptive budget multiplier remained fixed.
            </div>
            """,
            unsafe_allow_html=True,
        )

        baseline_configuration = pd.DataFrame(
            [
                {
                    "Setting": "Transactions evaluated",
                    "Baseline value": f"{int(baseline_params.get('limit', transaction_limit)):,}",
                },
                {
                    "Setting": "Analyst capacity",
                    "Baseline value": (
                        f"{int(baseline_params.get('alert_budget_per_step', alert_budget_per_step))} "
                        "alerts per operational step"
                    ),
                },
                {
                    "Setting": "Investigation cost",
                    "Baseline value": (
                        f"€{float(baseline_params.get('investigation_cost', investigation_cost)):,.2f} "
                        "per investigation"
                    ),
                },
                {
                    "Setting": "Static fraud threshold",
                    "Baseline value": (
                        f"{float(baseline_params.get('static_threshold', static_threshold)):.2f}"
                    ),
                },
                {
                    "Setting": "Minimum Adaptive fraud threshold",
                    "Baseline value": (
                        f"{float(baseline_params.get('risk_zone_floor', risk_zone_floor)):.2f}"
                    ),
                },
                {
                    "Setting": "Adaptive budget multiplier",
                    "Baseline value": (
                        f"{float(baseline_params.get('budget_multiplier', budget_multiplier)):.2f}"
                    ),
                },
                {
                    "Setting": "Suppression window",
                    "Baseline value": (
                        f"{int(baseline_params.get('suppression_window', suppression_window))} "
                        "operational steps"
                    ),
                },
            ]
        )

        st.markdown("#### Baseline configuration")
        st.dataframe(
            baseline_configuration,
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "How to read this table: the row belonging to the selected experiment is the "
            "setting that changes. All other rows remain fixed at these baseline values."
        )

        st.markdown("### What was tested?")
        st.markdown(
            """
            <div class="question-card">
                Seven different operating parameters were examined. For example, the tests
                changed analyst capacity, transaction volume, investigation cost and alert
                thresholds. Only one parameter was changed at a time, so any difference in
                the results can be linked to that specific setting.
            </div>
            """,
            unsafe_allow_html=True,
        )

        finding_kpi_1, finding_kpi_2, finding_kpi_3, finding_kpi_4 = st.columns(4)

        with finding_kpi_1:
            metric_card(
                "Independent experiments",
                f"{len(experiment_names)}",
                "One parameter changed per experiment; all others stayed fixed.",
                "blue",
            )

        with finding_kpi_2:
            metric_card(
                "Adaptive performed best",
                f"{overview_adaptive_families} / {len(experiment_names)}",
                adaptive_best_text,
                "green",
            )

        with finding_kpi_3:
            metric_card(
                "Static performed best",
                f"{overview_static_families} / {len(experiment_names)}",
                static_best_text,
                "orange",
            )

        with finding_kpi_4:
            metric_card(
                "No clear winner",
                f"{overview_tied_families}",
                tied_text,
                "blue",
            )

        combined_results = pd.concat(
            [
                pd.DataFrame(result_map[experiment_name])
                for experiment_name in experiment_names
            ],
            ignore_index=True,
        )

        total_adaptive = int((combined_results["winner"] == "Adaptive").sum())
        total_static = int((combined_results["winner"] == "Static").sum())
        total_ties = int((combined_results["winner"] == "Tie").sum())
        total_settings = len(combined_results)

        st.markdown("### Results across all tested settings")
        st.caption(
            "These figures summarise the individual operating configurations tested across the seven experiments."
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(
                "Settings tested",
                f"{total_settings}",
                "One parameter changed at a time.",
                "blue",
            )
        with c2:
            metric_card(
                "Adaptive preferable",
                f"{total_adaptive}",
                "Higher recall, or lower cost when recall tied.",
                "green",
            )
        with c3:
            metric_card(
                "Static preferable",
                f"{total_static}",
                "Higher recall, or lower cost when recall tied.",
                "orange",
            )
        with c4:
            metric_card(
                "Equivalent result",
                f"{total_ties}",
                "Same recall and effectively equal cost.",
                "blue",
            )

        st.markdown("### What do these results tell us?")

        adaptive_share = total_adaptive / total_settings if total_settings else 0.0

        insight_col_1, insight_col_2, insight_col_3 = st.columns(3)

        with insight_col_1:
            st.markdown(
                """
                <div class="definition-card">
                    <strong>1. Analyst capacity changes the value of the policy</strong>
                    <p>
                    When analyst capacity is very limited, Static and Adaptive can become
                    operationally equivalent because too few alerts can reach investigation.
                    As capacity increases, the benefit of better prioritisation can become visible.
                    </p>
                    <div class="small">
                        <strong>Main implication:</strong> better model scores alone are not enough;
                        operational value depends on the resources available to act on them.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with insight_col_2:
            st.markdown(
                """
                <div class="definition-card">
                    <strong>2. Adaptive performance depends on how it is configured</strong>
                    <p>
                    Low Adaptive budget multipliers underperformed Static, while performance
                    improved from approximately 1.3 and stabilised around 1.4 and above.
                    The Minimum Adaptive threshold also performed best within a middle range,
                    showing that both how broadly Adaptive selects alerts and the minimum score
                    required for selection affect its performance.
                    </p>
                    <div class="small">
                        <strong>Main implication:</strong> Adaptive is not automatically better;
                        its advantage depends on appropriate operational tuning.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with insight_col_3:
            st.markdown(
                """
                <div class="definition-card">
                    <strong>3. Not every operational setting has the same impact</strong>
                    <p>
                    Changing the suppression window produced little change in fraud detection
                    in the current sample, while analyst capacity and policy thresholds produced
                    much larger differences between Static and Adaptive.
                    </p>
                    <div class="small">
                        <strong>Main implication:</strong> some controls materially affect the
                        decision outcome, while others mainly support workload management.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="takeaway">
                <strong>Overall interpretation</strong><br>
                Adaptive was preferred in <strong>{total_adaptive} of {total_settings}
                tested settings ({adaptive_share:.1%})</strong>, but the sensitivity analysis
                shows that its advantage is <strong>conditional rather than universal</strong>.
                The strongest overall conclusion is that fraud-decision performance depends on
                the interaction between <strong>alert-selection strategy, analyst capacity and
                operating parameters</strong> — not on the machine-learning score alone.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Evidence behind the findings")
        st.caption(
            "Open the full table to inspect every tested configuration and the calculations behind the conclusions."
        )

        with st.expander("View full comparison across all 45 tested settings", expanded=False):

            st.markdown(
                """
                The table below shows the **individual calculation for every tested setting**,
                rather than another summary of which experiment won overall. This makes it possible
                to compare how Static and Adaptive behaved under each operating condition.
                """
            )

            full_comparison = combined_results[[
                "experiment",
                "value",
                "static_investigated",
                "adaptive_investigated",
                "static_detected",
                "adaptive_detected",
                "static_recall",
                "adaptive_recall",
                "recall_difference",
                "static_cost",
                "adaptive_cost",
                "adaptive_cost_saving",
                "static_overflow",
                "adaptive_overflow",
                "adaptive_suppressed",
                "winner",
            ]].copy()

            experiment_order = {name: position for position, name in enumerate(experiment_names)}
            full_comparison["_experiment_order"] = full_comparison["experiment"].map(experiment_order)
            full_comparison = full_comparison.sort_values(
                ["_experiment_order", "value"]
            ).drop(columns="_experiment_order")

            full_comparison["static_recall"] = full_comparison["static_recall"].map(pct)
            full_comparison["adaptive_recall"] = full_comparison["adaptive_recall"].map(pct)
            full_comparison["recall_difference"] = full_comparison["recall_difference"].map(
                lambda value: f"{value:+.2%}"
            )

            for cost_column in [
                "static_cost",
                "adaptive_cost",
                "adaptive_cost_saving",
            ]:
                full_comparison[cost_column] = full_comparison[cost_column].map(money)

            full_comparison = full_comparison.rename(
                columns={
                    "experiment": "Experiment",
                    "value": "Tested value",
                    "static_investigated": "Static investigated",
                    "adaptive_investigated": "Adaptive investigated",
                    "static_detected": "Static frauds detected",
                    "adaptive_detected": "Adaptive frauds detected",
                    "static_recall": "Static recall",
                    "adaptive_recall": "Adaptive recall",
                    "recall_difference": "Adaptive recall Δ",
                    "static_cost": "Static estimated cost",
                    "adaptive_cost": "Adaptive estimated cost",
                    "adaptive_cost_saving": "Adaptive cost saving",
                    "static_overflow": "Static overflow",
                    "adaptive_overflow": "Adaptive overflow",
                    "adaptive_suppressed": "Adaptive suppressed",
                    "winner": "Preferred policy",
                }
            )

            st.dataframe(
                full_comparison,
                width="stretch",
                hide_index=True,
                height=720,
            )

            st.caption(
                "Adaptive recall Δ = Adaptive recall − Static recall. "
                "Adaptive cost saving = Static estimated operational cost − Adaptive estimated operational cost; "
                "a positive value therefore favours Adaptive. Preferred policy is determined by higher recall, "
                "with lower estimated operational cost used when recall is tied."
            )


        st.markdown("### Drill down into one experiment")
        st.caption(
            "Use this drill-down to inspect how one operating parameter changes recall, estimated cost and policy preference across its tested values."
        )
        selected_experiment = st.selectbox(
            "Select the parameter you want to inspect",
            experiment_names,
            key="educational_sensitivity_selector",
        )
        selected_definition = experiment_definitions[selected_experiment]
        selected_frame = pd.DataFrame(result_map[selected_experiment]).sort_values("value")

        st.markdown(
            f"""
            <div class="question-card">
                <strong>{html.escape(selected_experiment)}</strong><br>
                <strong>Values tested:</strong> {html.escape(selected_definition['display_values'])}<br>
                <strong>Question answered:</strong> {html.escape(selected_definition['purpose'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        chart_frame = selected_frame[["value", "static_recall", "adaptive_recall"]].copy()
        chart_frame["static_recall"] = chart_frame["static_recall"] * 100
        chart_frame["adaptive_recall"] = chart_frame["adaptive_recall"] * 100
        chart_frame = chart_frame.set_index("value").rename(
            columns={
                "static_recall": "Static recall",
                "adaptive_recall": "Adaptive recall",
            }
        )

        x_axis_labels = {
            "Transaction volume": "Transaction volume (transactions)",
            "Analyst capacity": "Analyst capacity (alerts per operational step)",
            "Investigation cost": "Investigation cost (€ per investigation)",
            "Suppression window": "Suppression window (operational steps)",
            "Adaptive budget multiplier": "Adaptive budget multiplier",
            "Static threshold": "Static fraud threshold",
            "Minimum Adaptive threshold": "Minimum Adaptive fraud threshold",
        }

        st.line_chart(
            chart_frame,
            x_label=x_axis_labels[selected_experiment],
            y_label="Fraud recall (%)",
            width="stretch",
        )

        detail_display = selected_frame[[
            "value",
            "static_recall",
            "adaptive_recall",
            "recall_difference",
            "static_cost",
            "adaptive_cost",
            "adaptive_cost_saving",
            "winner",
        ]].copy()
        detail_display["static_recall"] = detail_display["static_recall"].map(pct)
        detail_display["adaptive_recall"] = detail_display["adaptive_recall"].map(pct)
        detail_display["recall_difference"] = detail_display["recall_difference"].map(
            lambda value: f"{value:+.2%}"
        )
        for cost_column in ["static_cost", "adaptive_cost", "adaptive_cost_saving"]:
            detail_display[cost_column] = detail_display[cost_column].map(money)
        detail_display = detail_display.rename(
            columns={
                "value": "Tested value",
                "static_recall": "Static recall",
                "adaptive_recall": "Adaptive recall",
                "recall_difference": "Adaptive recall difference",
                "static_cost": "Static estimated operational cost (€)",
                "adaptive_cost": "Adaptive estimated operational cost (€)",
                "adaptive_cost_saving": "Estimated Adaptive cost saving (€)",
                "winner": "Preferred policy",
            }
        )
        st.dataframe(detail_display, width="stretch", hide_index=True)
        st.caption(
            "Sensitivity cost values are simulation estimates. They are used to compare "
            "policies under identical assumptions rather than to claim observed banking losses."
        )

        selected_interpretations = {
            "Transaction volume": (
                "The effect of policy choice changes with workload size. At smaller transaction volumes, "
                "the two policies produced similar fraud coverage, while the larger workload exposed a clearer "
                "Adaptive advantage. This indicates that workload scale can change the operational value of prioritisation."
            ),
            "Analyst capacity": (
                "At very low analyst capacity, both policies achieve the same recall because too few alerts can reach "
                "investigation. Adaptive gains an advantage at several intermediate capacity levels, but the pattern is "
                "not monotonic. Capacity therefore changes the value of prioritisation rather than improving both policies uniformly."
            ),
            "Investigation cost": (
                "Changing the assumed cost per investigation changes the economic comparison but not fraud recall or alert "
                "selection in this experiment. The parameter therefore affects the estimated financial consequence of the "
                "decision rather than the detection behaviour itself."
            ),
            "Suppression window": (
                "Changing the suppression window produces little change in fraud recall in the current sample. Its main role "
                "here is workload management rather than materially changing which policy detects more fraud."
            ),
            "Adaptive budget multiplier": (
                "Low Adaptive budget multipliers restrict candidate selection enough for Static to perform better. Adaptive "
                "improves from approximately 1.3 and stabilises around 1.4 and above, suggesting a useful operating region "
                "followed by diminishing returns."
            ),
            "Static threshold": (
                "Static performance is highly sensitive to the chosen fixed threshold. Moving the cut-off materially changes "
                "fraud recall and can reverse the preferred policy, showing why a single fixed threshold should not be treated "
                "as universally optimal."
            ),
            "Minimum Adaptive threshold": (
                "Adaptive performs best within an intermediate threshold range rather than at the extremes. A threshold that "
                "is too low admits weaker candidates, while a high threshold makes Adaptive increasingly restrictive. The "
                "result supports tuning the minimum Adaptive threshold rather than assuming that lower or higher is always better."
            ),
        }

        selected_interpretation = selected_interpretations.get(
            selected_experiment,
            build_plain_finding(selected_frame),
        )

        st.markdown(
            f"""
            <div class="chart-conclusion">
                <strong>Drill-down interpretation</strong><br>
                {html.escape(selected_interpretation)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Sensitivity-analysis technical details"):
            st.json(
                {
                    "method": "one-at-a-time parameter sensitivity",
                    "comparison_rule": "higher recall; lower cost used only when recall is tied",
                    "parameter_families": experiment_names,
                    "total_tested_settings": total_settings,
                    "fixed_settings": "Current sidebar values except the parameter under test",
                    "endpoint": "/simulation/sensitivity",
                    "execution_metadata": saved_analysis.get(
                        "execution_metadata", {}
                    ),
                }
            )