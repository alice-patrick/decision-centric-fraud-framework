from __future__ import annotations

import html
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

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


def get_summary(
    payload: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    return payload.get(key, {}).get("summary", {})


def normalise_windows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

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
def load_sensitivity_data(base_params: dict[str, Any]) -> dict[str, Any]:
    """Run all sensitivity experiments through one optimized API request."""
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
                "static_overflow": i(row.get("static_capacity_rejected_alerts")),
                "adaptive_overflow": i(row.get("adaptive_capacity_rejected_alerts")),
                "adaptive_suppressed": i(row.get("adaptive_suppressed_alerts")),
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
            This dashboard tells the story of how suspicious transactions move from a machine-learning score to human investigation. It is designed for users with no previous knowledge of fraud detection.
        </p>
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
        [1000, 3000, 10000, 50000],
        index=2,
        help=(
            "How many transactions are included in the current simulation."
        ),
    )

    alert_budget_per_step = st.number_input(
        "Alerts allowed per operational step",
        min_value=1,
        max_value=5000,
        value=50,
        step=5,
        help=(
            "Maximum number of cases analysts can review during each "
            "simulation decision window."
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
        "Cost per investigation",
        min_value=0.0,
        value=10.0,
        step=1.0,
        help="Assumed cost of reviewing one alert.",
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
# QUICK USER GUIDE — ABOVE THE TABS
# =========================================================

st.markdown(
    """
    <div style="
        max-width: 720px;
        margin: 0 0 .7rem 0;
        padding: .55rem .8rem;
        border-left: 3px solid #1976d2;
        border-radius: 8px;
        background: rgba(25,118,210,.07);
        font-size: .88rem;
        line-height: 1.45;
    ">
        <strong>Quick tip</strong><br>
        The experiment settings are available in the left sidebar.
        Change one parameter at a time for a meaningful comparison.
    </div>
    """,
    unsafe_allow_html=True,
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
            This page compares the Static and Adaptive alert-selection policies
            under ideal Batch conditions and under Sequential operational constraints.
        </div>
        """,
        unsafe_allow_html=True,
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
    static_investigated_alerts = i(static_seq.get("selected_alerts"))
    adaptive_batch_alerts = i(adaptive_batch.get("selected_alerts"))
    adaptive_investigated_alerts = i(adaptive_seq.get("selected_alerts"))

    st.markdown("### Experiment overview")

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        metric_card(
            "Frauds in dataset",
            f"{total_frauds:,}",
            "Known fraud cases in the evaluated transaction sample.",
            "blue",
        )

    with k2:
        metric_card(
            "Static frauds detected",
            f"{static_batch_frauds} → {static_seq_frauds}",
            "Batch result followed by Sequential result.",
            "orange",
        )

    with k3:
        metric_card(
            "Adaptive frauds detected",
            f"{adaptive_batch_frauds} → {adaptive_seq_frauds}",
            "Batch result followed by Sequential result.",
            "green",
        )

    with k4:
        metric_card(
            "Static alerts selected",
            f"{static_batch_alerts:,} → {static_investigated_alerts:,}",
            "Batch alerts followed by alerts investigated in Sequential replay.",
            "orange",
        )

    with k5:
        metric_card(
            "Adaptive alerts selected",
            f"{adaptive_batch_alerts:,} → {adaptive_investigated_alerts:,}",
            "Batch alerts followed by alerts investigated in Sequential replay.",
            "blue",
        )

    st.markdown("### Main comparison")

    main_chart = pd.DataFrame(
        [
            {
                "Scenario": "Batch",
                "Static": static_batch_frauds,
                "Adaptive": adaptive_batch_frauds,
            },
            {
                "Scenario": "Sequential",
                "Static": static_seq_frauds,
                "Adaptive": adaptive_seq_frauds,
            },
        ]
    ).set_index("Scenario")

    chart_col, note_col = st.columns([2.1, 1])

    with chart_col:
        st.bar_chart(
            main_chart,
            width="stretch",
        )

    batch_fraud_gain = adaptive_batch_frauds - static_batch_frauds
    seq_fraud_gain = adaptive_seq_frauds - static_seq_frauds

    with note_col:
        st.markdown(
            f"""
            <div class="takeaway">
                <strong>Key finding</strong><br>
                Adaptive detects <strong>{batch_fraud_gain:+,}</strong> additional
                fraud cases before operational constraints and
                <strong>{seq_fraud_gain:+,}</strong> additional fraud cases after
                the analyst queue is applied.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Exact results")

    comparison_table = pd.DataFrame(
        [
            {
                "Scenario": "Static Batch",
                "Alerts": i(static_batch.get("selected_alerts")),
                "Frauds detected": static_batch_frauds,
                "Frauds missed": i(static_batch.get("frauds_missed")),
                "Precision": n(static_batch.get("precision")),
                "Recall": n(static_batch.get("recall")),
                "Operational cost": n(
                    static_batch.get("total_operational_cost")
                ),
            },
            {
                "Scenario": "Adaptive Batch",
                "Alerts": i(adaptive_batch.get("selected_alerts")),
                "Frauds detected": adaptive_batch_frauds,
                "Frauds missed": i(adaptive_batch.get("frauds_missed")),
                "Precision": n(adaptive_batch.get("precision")),
                "Recall": n(adaptive_batch.get("recall")),
                "Operational cost": n(
                    adaptive_batch.get("total_operational_cost")
                ),
            },
            {
                "Scenario": "Static Sequential",
                "Alerts": i(static_seq.get("selected_alerts")),
                "Frauds detected": static_seq_frauds,
                "Frauds missed": i(static_seq.get("frauds_missed")),
                "Precision": n(static_seq.get("precision")),
                "Recall": n(static_seq.get("recall")),
                "Operational cost": n(
                    static_seq.get("total_operational_cost")
                ),
            },
            {
                "Scenario": "Adaptive Sequential",
                "Alerts": adaptive_investigated_alerts,
                "Frauds detected": adaptive_seq_frauds,
                "Frauds missed": i(adaptive_seq.get("frauds_missed")),
                "Precision": n(adaptive_seq.get("precision")),
                "Recall": n(adaptive_seq.get("recall")),
                "Operational cost": n(
                    adaptive_seq.get("total_operational_cost")
                ),
            },
        ]
    )

    comparison_display = comparison_table.copy()
    comparison_display["Precision"] = comparison_display["Precision"].map(pct)
    comparison_display["Recall"] = comparison_display["Recall"].map(pct)
    comparison_display["Operational cost"] = (
        comparison_display["Operational cost"].map(money)
    )

    table_col, table_note_col = st.columns([2.25, 1])

    with table_col:
        st.dataframe(
            comparison_display,
            width="stretch",
            hide_index=True,
        )

    batch_recall_gain = (
        n(adaptive_batch.get("recall"))
        - n(static_batch.get("recall"))
    )
    sequential_recall_gain = (
        n(adaptive_seq.get("recall"))
        - n(static_seq.get("recall"))
    )

    with table_note_col:
        st.markdown(
            f"""
            <div class="takeaway">
                <strong>Interpretation</strong><br>
                Adaptive changes recall by
                <strong>{batch_recall_gain:+.2%}</strong> in Batch evaluation and by
                <strong>{sequential_recall_gain:+.2%}</strong> after Sequential
                constraints are introduced.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Batch versus Sequential performance")

    before_after = pd.DataFrame(
        [
            {
                "Policy": "Static",
                "Batch recall": n(static_batch.get("recall")),
                "Sequential recall": n(static_seq.get("recall")),
                "Batch precision": n(static_batch.get("precision")),
                "Sequential precision": n(static_seq.get("precision")),
            },
            {
                "Policy": "Adaptive",
                "Batch recall": n(adaptive_batch.get("recall")),
                "Sequential recall": n(adaptive_seq.get("recall")),
                "Batch precision": n(adaptive_batch.get("precision")),
                "Sequential precision": n(adaptive_seq.get("precision")),
            },
        ]
    )

    before_after_display = before_after.copy()

    for column in [
        "Batch recall",
        "Sequential recall",
        "Batch precision",
        "Sequential precision",
    ]:
        before_after_display[column] = (
            before_after_display[column].map(pct)
        )

    performance_col, explanation_col = st.columns([1.75, 1])

    with performance_col:
        st.dataframe(
            before_after_display,
            width="stretch",
            hide_index=True,
        )

    with explanation_col:
        st.markdown(
            """
            <div class="warning">
                <strong>Why do the metrics change?</strong><br>
                Batch assumes that every selected alert can be reviewed.
                Sequential simulation introduces analyst capacity, chronological
                arrival and suppression. The ML model is unchanged; the operating
                environment is more restrictive.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="takeaway">
            <strong>Key observation</strong><br>
            Before operational constraints, Adaptive detects more fraudulent
            transactions. After analyst capacity and suppression are applied,
            recall falls for both policies, showing how limited investigation
            resources reduce the performance that can be realised in practice.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Static and Adaptive in simple terms")

    p1, p2 = st.columns(2)

    with p1:
        concept_card(
            "Static fraud threshold",
            (
                "Uses one fixed score threshold for every transaction."
            ),
            (
                "Simple, stable and predictable, but it does not adapt its "
                "selection to workload or capacity."
            ),
        )

    with p2:
        concept_card(
            "Adaptive fraud threshold policy",
            (
                "Uses a minimum threshold together with risk-zone and "
                "operational-priority logic."
            ),
            (
                "Can capture more useful candidates, but the extra alerts create "
                "value only when sufficient analyst capacity exists."
            ),
        )

    sequential_cost_saving = (n(static_seq.get("total_operational_cost"))
        - n(adaptive_seq.get("total_operational_cost"))
    )

    if sequential_cost_saving > 0:
        cost_phrase = (
            f"and lowers total operational cost by "
            f"{money(sequential_cost_saving)}"
        )
    elif sequential_cost_saving < 0:
        cost_phrase = (
            f"but increases total operational cost by "
            f"{money(abs(sequential_cost_saving))}"
        )
    else:
        cost_phrase = "with no change in total operational cost"

    st.markdown(
        f"""
        <div class="takeaway">
            <strong>Overall result</strong><br>
            Adaptive detects <strong>{batch_fraud_gain:+,}</strong> additional fraud
            cases before the analyst queue and
            <strong>{seq_fraud_gain:+,}</strong> after Sequential constraints,
            {html.escape(cost_phrase)}. Under the current configuration, this is the
            main operational difference between the two policies.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if sequential_recall_gain > 0 and sequential_cost_saving > 0:
        recommendation = (
            "Adaptive is preferred under the current configuration because it "
            "combines higher Sequential recall with lower operational cost."
        )
    elif sequential_recall_gain > 0:
        recommendation = (
            "Adaptive improves fraud coverage, but management should review the "
            "additional cost and workload before selecting it."
        )
    elif sequential_recall_gain < 0:
        recommendation = (
            "Static performs better on Sequential recall under the current "
            "configuration. Adaptive settings should be reviewed before use."
        )
    else:
        recommendation = (
            "The policies provide equal Sequential recall. Prefer the lower-cost "
            "or simpler option unless another operational objective justifies Adaptive."
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

            **Batch evaluation:** measures theoretical policy performance without
            chronological replay, suppression or per-step analyst-capacity constraints.

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

            **Operational cost:** investigation cost plus the estimated cost of fraud
            cases that were missed.

            **Operational step:** one chronological decision cycle of the sequential
            replay. Suppression, ranking and analyst capacity are applied independently
            within each step before the replay continues.

            **Parameter setting:** one specific tested value of an operational
            parameter during the sensitivity analysis.

            **Precision:** the share of investigated alerts that were truly fraudulent.

            **Preferred policy:** the policy judged more favourable for one tested
            setting. The dashboard compares recall first and uses lower operational
            cost only when recall is equal.

            **Recall:** the share of all real fraud cases detected.

            **Robustness:** the ability of the decision layer to produce reasonable and
            explainable results across different operational configurations.

            **Sensitivity analysis:** evaluates how system behaviour changes when one
            operational parameter is modified while the remaining settings stay fixed.

            **Sequential simulation:** measures how much theoretical policy performance
            survives chronology, suppression and limited analyst capacity.

            **Static fraud threshold:** the fixed fraud-risk score above which a
            transaction becomes a candidate alert under the Static policy.

            **Suppression:** filters repeated alerts for the same simulated entity
            within the configured suppression window before analyst capacity is applied.

            **Tested value:** one individual parameter value evaluated during a
            sensitivity experiment.

            **Tie:** a tested setting where Static and Adaptive produce equal recall and
            effectively equal operational cost.

            **Trade-off:** a situation where one policy improves one objective while
            worsening another, such as higher recall with higher cost.

            **Transaction volume:** the number of historical transactions included in
            one simulation experiment.

            **Transactions evaluated:** the number of historical transactions included
            in the current simulation replay.

            **Winner:** the Static or Adaptive policy that produces the more favourable
            result under the dashboard's comparison rule for one tested setting.

            **One-at-a-time experiment:** an experiment where only one parameter changes
            between runs so that its effect can be isolated.
            """
        )

    with st.expander("Technical details"):
        st.markdown("#### Experimental dataset")
        st.markdown(
            """
            **Dataset:** PaySim synthetic payment transaction dataset  \n            **Evaluation mode:** Offline historical replay  \n            **Processing:** Chronological sequential simulation using the dataset's `step` variable  \n            **Purpose:** Evaluation of fraud-detection and operational decision-making strategies under controlled experimental conditions  \n            **Environment:** Research prototype; the results do not originate from a live banking production system

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
                "static_batch_frauds": static_batch_frauds,
                "adaptive_batch_frauds": adaptive_batch_frauds,
                "static_sequential_frauds": static_seq_frauds,
                "adaptive_sequential_frauds": adaptive_seq_frauds,
                "adaptive_investigated_alerts": adaptive_investigated_alerts,
            }
        )


# =========================================================
# 3. ANALYST CAPACITY
# =========================================================

with capacity_tab:
    st.header("Analyst Capacity by Policy")

    st.caption(
        "Select a policy to see how the same analyst-capacity constraint "
        "affects its candidate alerts and investigation queue."
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

    candidates = i(
        selected_summary.get("policy_candidate_alerts")
    )
    accepted = i(
        selected_summary.get("selected_alerts")
    )
    suppressed = i(
        selected_summary.get("suppressed_alerts")
    )
    rejected = i(
        selected_summary.get("capacity_rejected_alerts")
    )

    unique_steps = i(parameters.get("unique_steps"))
    maximum_capacity = i(
        parameters.get(
            "maximum_sequential_capacity",
            int(alert_budget_per_step) * unique_steps,
        )
    )

    eligible_after_suppression = max(
       candidates - suppressed,
       0,
    )

    budget_overflow = rejected

    # Results first.
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        metric_card(
            "Candidate alerts",
            f"{candidates:,}",
            f"Initially proposed by the {policy_choice} policy.",
            "blue",
        )

    with k2:
        metric_card(
            "Investigated alerts",
            f"{accepted:,}",
            "Actually entered the analyst queue.",
            "green",
        )

    with k3:
        metric_card(
            "Suppressed alerts",
            f"{suppressed:,}",
            "Filtered as repeated entity alerts.",
            "orange",
        )

    with k4:
        metric_card(
             "Budget overflow",
             f"{rejected:,}",
             "Candidate alerts that could not be investigated because the analyst budget was exhausted.",
             "red",
        )

    st.markdown("### How were the investigated alerts calculated?")

    st.markdown(
        f"""
        <div class="capacity-step-intro">
            <strong>What does “step” mean here?</strong><br>
            In this dashboard, a <strong>step is one chronological decision cycle in the replay</strong>.
            Transactions assigned to the same step are evaluated together before the replay
            moves to the next step. The current replay contains
            <strong>{unique_steps} operational steps</strong>, and analyst capacity is applied
            independently inside each one. A step should not be interpreted as a fixed real-world hour.
        </div>
        """,
        unsafe_allow_html=True,
    )

    step_col1, step_col2, step_col3 = st.columns(3)

    with step_col1:
        st.markdown(
            f"""
            <div class="capacity-step-card tone-blue">
                <strong>Replay unit</strong>
                <div class="step-value">1 step = 1 decision cycle</div>
                <div class="small">
                    Transactions in the same step are processed together before the replay continues.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with step_col2:
        st.markdown(
            f"""
            <div class="capacity-step-card tone-green">
                <strong>Capacity per step</strong>
                <div class="step-value">{int(alert_budget_per_step)} alerts maximum</div>
                <div class="small">
                    The analyst limit resets when the replay moves to the next step.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with step_col3:
        st.markdown(
            """
            <div class="capacity-step-card tone-orange">
                <strong>No capacity carry-over</strong>
                <div class="step-value">Unused slots expire</div>
                <div class="small">
                    Spare capacity in one step cannot be transferred to a later step.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        "Within every step, the sequence is: candidate alerts → suppression → "
        "priority ranking → analyst-capacity limit."
    )

    f1, a1, f2, a2, f3, a3, f4 = st.columns(
        [1, .14, 1, .14, 1, .14, 1]
    )

    with f1:
        funnel_card(
            "Candidate alerts",
            f"{candidates:,}",
            "Proposed before suppression and capacity.",
        )

    with a1:
        st.markdown(
            '<div class="funnel-arrow">→</div>',
            unsafe_allow_html=True,
        )

    with f2:
        funnel_card(
            "Eligible after suppression",
            f"{eligible_after_suppression:,}",
            f"{suppressed:,} repeated alerts were removed.",
        )

    with a2:
        st.markdown(
            '<div class="funnel-arrow">→</div>',
            unsafe_allow_html=True,
        )

    with f3:
        funnel_card(
            "Maximum analyst capacity",
            f"{maximum_capacity:,} investigations",
            (
                f"{int(alert_budget_per_step)} alerts per step × "
                f"{unique_steps} PaySim steps"
            ),
        )

    with a3:
        st.markdown(
            '<div class="funnel-arrow">→</div>',
            unsafe_allow_html=True,
        )

    with f4:
        funnel_card(
            "Actual investigated alerts",
            f"{accepted:,}",
            "Highest-priority alerts accepted across all steps.",
        )

    st.markdown("### Step-by-step calculation")

    calculation_table = pd.DataFrame(
        [
            {
                "Stage": "1. Candidate alerts",
                "Explanation": "Alerts generated by the selected policy",
                "Value": candidates,
            },
            {
                "Stage": "2. Suppressed alerts",
                "Explanation": "Repeated alerts removed",
                "Value": -suppressed,
            },
            {
                "Stage": "3. Eligible alerts",
                "Explanation": "Candidate alerts remaining after suppression",
                "Value": eligible_after_suppression,
            },
            {
                "Stage": "4. Operational steps",
                "Explanation": "Chronological PaySim steps in the replay",
                "Value": unique_steps,
            },
            {
                "Stage": "5. Analyst capacity per step",
                "Explanation": "Maximum alerts investigated in each step",
                "Value": int(alert_budget_per_step),
            },
            {
                "Stage": "6. Maximum possible investigations",
                "Explanation": f"{int(alert_budget_per_step)} × {unique_steps}",
                "Value": maximum_capacity,
            },
            {
                "Stage": "7. Actual investigated alerts",
                "Explanation": "Alerts accepted into the analyst queue",
                "Value": accepted,
            },
            {
                "Stage": "8. Budget overflow",
                "Explanation": "Eligible alerts that could not be investigated",
                "Value": budget_overflow,
            },
        ]
    )

    st.dataframe(
        calculation_table,
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        f"""
        <div class="takeaway">
            <strong>Why were only {accepted:,} alerts investigated instead of {maximum_capacity:,}?</strong>
            <br><br>
            The analyst team could theoretically investigate up to
            <strong>{maximum_capacity:,}</strong> alerts
            ({int(alert_budget_per_step)} alerts × {unique_steps} operational steps).
            <br><br>
            However, analyst capacity is enforced separately inside every operational step.
            Some steps contained fewer eligible alerts after suppression, while other steps
            contained more alerts than analysts could review.
            <br><br>
            Because unused capacity from one operational step cannot be transferred to a later
            step, the replay finished with <strong>{accepted:,}</strong> investigated alerts
            instead of the theoretical maximum of <strong>{maximum_capacity:,}</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Operational step breakdown")

    selected_payload = (
        data.get("static_sequential", {})
        if policy_choice == "Static"
        else data.get("adaptive_sequential", {})
    )

    step_records = selected_payload.get("operational_steps", [])
    step_frame = pd.DataFrame(step_records)

    if step_frame.empty:
        st.info(
            "No operational-step records were returned by the API. Restart the "
            "FastAPI service after replacing both `sequential.py` and the simulation "
            "API file with the updated versions."
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
            "capacity_status",
        }
        missing_step_columns = sorted(
            required_step_columns - set(step_frame.columns)
        )

        if missing_step_columns:
            st.warning(
                "Operational-step data were returned, but required fields are "
                f"missing: {missing_step_columns}"
            )
        else:
            step_frame = step_frame.sort_values("step").reset_index(drop=True)

            # Keep the visible table focused on the six values needed to
            # explain how the per-step analyst limit produced the final result.
            step_breakdown = pd.DataFrame(
                {
                    "Step": step_frame["step"].map(i),
                    "Candidate": step_frame["candidate_alerts"].map(i),
                    "Suppressed": step_frame["suppressed_alerts"].map(i),
                    "Eligible": step_frame["eligible_alerts"].map(i),
                    "Investigated": step_frame["investigated_alerts"].map(i),
                    "Overflow": step_frame[
                        "capacity_rejected_alerts"
                    ].map(i),
                }
            )

            totals_row = pd.DataFrame(
                [
                    {
                        "Step": "Total",
                        "Candidate": int(step_breakdown["Candidate"].sum()),
                        "Suppressed": int(step_breakdown["Suppressed"].sum()),
                        "Eligible": int(step_breakdown["Eligible"].sum()),
                        "Investigated": int(
                            step_breakdown["Investigated"].sum()
                        ),
                        "Overflow": int(step_breakdown["Overflow"].sum()),
                    }
                ]
            )
            step_breakdown = pd.concat(
                [step_breakdown, totals_row],
                ignore_index=True,
            )

            st.dataframe(
                step_breakdown,
                width="stretch",
                hide_index=True,
            )

            # Use the API fields, rather than the displayed totals row, to
            # describe overload and unused capacity accurately.
            overloaded_steps = int(
                (step_frame["capacity_rejected_alerts"].map(i) > 0).sum()
            )
            underused_steps = int(
                (step_frame["unused_capacity"].map(i) > 0).sum()
            )
            fully_used_steps = int(
                (
                    (step_frame["capacity_rejected_alerts"].map(i) == 0)
                    & (step_frame["unused_capacity"].map(i) == 0)
                ).sum()
            )

            st.markdown(
                f"""
                <div class="info-box">
                    <strong>How to read this table</strong><br><br>
                    <strong>{overloaded_steps}</strong> operational steps exceeded the
                    analyst limit and produced budget overflow.
                    <strong>{underused_steps}</strong> steps finished with unused capacity,
                    while <strong>{fully_used_steps}</strong> used exactly the available
                    limit without rejecting additional alerts.
                    <br><br>
                    Eligible alerts are candidate alerts remaining after suppression.
                    When eligible alerts exceed
                    <strong>{int(alert_budget_per_step)}</strong>, only the highest-priority
                    alerts are investigated and the remainder become budget overflow.
                </div>
                """,
                unsafe_allow_html=True,
            )

    outcome_table = pd.DataFrame(
        [
            {
                "Outcome": "Investigated",
                "Alerts": accepted,
                "Share of candidates": (
                    accepted / candidates if candidates else 0.0
                ),
            },
            {
                "Outcome": "Suppressed",
                "Alerts": suppressed,
                "Share of candidates": (
                    suppressed / candidates if candidates else 0.0
                ),
            },
            {
                "Outcome": "Capacity rejected",
                "Alerts": rejected,
                "Share of candidates": (
                    rejected / candidates if candidates else 0.0
                ),
            },
        ]
    )

    st.markdown("### Alert outcomes")
    st.bar_chart(
        outcome_table.set_index("Outcome")[["Alerts"]],
        width="stretch",
    )

    acceptance_rate = (
        accepted / candidates
        if candidates else 0.0
    )
    rejection_rate = (
        rejected / candidates
        if candidates else 0.0
    )

    st.markdown(
        f"""
        <div class="takeaway">
            <strong>Interpretation</strong><br>
            Analysts reviewed <strong>{acceptance_rate:.1%}</strong> of the
            <strong>{html.escape(policy_choice)}</strong> candidate alerts, while
            <strong>{rejection_rate:.1%}</strong> were rejected for capacity.
            This shows how much of the selected policy's proposed workload could
            actually reach human investigation.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Key observation</strong><br>
            With the current limit of
            <strong>{int(alert_budget_per_step)}</strong> alerts per PaySim step,
            <strong>{accepted:,}</strong> of
            <strong>{candidates:,}</strong>
            <strong>{html.escape(policy_choice)}</strong> candidate alerts reached
            investigation. The policy selector allows the same capacity mechanism
            to be examined for both Static and Adaptive under an identical setting.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if rejected > accepted:
        capacity_recommendation = (
            f"Capacity is highly restrictive for the {policy_choice} policy. "
            "Test more analyst slots, stronger prioritisation or narrower "
            "candidate generation before expanding the alert workload."
        )
    elif rejected > 0:
        capacity_recommendation = (
            f"Some {policy_choice} candidate workload remains outside the queue. "
            "A moderate increase in capacity or improved ranking may increase "
            "fraud coverage."
        )
    else:
        capacity_recommendation = (
            f"Capacity is not currently the main bottleneck for the "
            f"{policy_choice} policy. Focus on precision and investigation cost."
        )

    st.markdown(
        f"""
        <div class="decision-box">
            <strong>Management recommendation</strong><br>
            {html.escape(capacity_recommendation)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Technical details"):
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
                "budget_overflow": budget_overflow,
                "capacity_rejected": rejected,
            }
        )


# =========================================================
# 4. SEQUENTIAL WORKFLOW
# =========================================================

with workflow_tab:
    st.header("Sequential Workflow")

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

    st.markdown(
        """
        <div class="info-box">
            <strong>Why is this important?</strong><br>
            Sequential replay introduces operational constraints that are absent
            from a simple Batch evaluation.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Batch versus Sequential")

    comparison_table = pd.DataFrame(
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

    st.dataframe(
        comparison_table,
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        """
        <div class="info-box">
            <strong>Interpretation</strong><br>
            Batch measures theoretical policy quality. Sequential simulation measures
            how much of that benefit survives chronology, suppression and limited
            analyst capacity.
        </div>
        """,
        unsafe_allow_html=True,
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
                "operational_cost": "Operational cost",
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
                workload peaks, missed fraud and changes in operational cost.
            </div>
            """,
            unsafe_allow_html=True,
        )

        def trend_label(series: pd.Series) -> str:
            clean = pd.to_numeric(series, errors="coerce").dropna()

            if len(clean) < 2:
                return "Insufficient data"

            first_value = float(clean.iloc[0])
            last_value = float(clean.iloc[-1])
            mean_value = float(clean.mean())
            value_range = float(clean.max() - clean.min())

            if mean_value == 0:
                return "Stable" if value_range == 0 else "Variable"

            relative_change = (last_value - first_value) / abs(mean_value)
            relative_range = value_range / abs(mean_value)

            if relative_range < 0.15:
                return "Stable"
            if relative_change > 0.15:
                return "Generally increasing"
            if relative_change < -0.15:
                return "Generally decreasing"
            return "Variable"

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
            title="Operational Cost per Monitoring Window",
            y_axis_label="Operational Cost (€)",
            value_formatter=lambda value: f"€{value:,.2f}",
            interpretation=(
                "This chart combines investigation workload with the cost assigned "
                "to missed fraud. Cost peaks reveal the periods with the greatest "
                "overall operational impact."
            ),
        )

        # Overall monitoring conclusion.
        candidate_peak_text = "not available"
        rejected_peak_text = "not available"
        missed_peak_text = "not available"
        cost_peak_text = "not available"

        if "candidate_alerts" in adaptive_windows.columns:
            row = adaptive_windows.loc[
                adaptive_windows["candidate_alerts"].idxmax()
            ]
            candidate_peak_text = (
                f"Monitoring Window {i(row['window'])} "
                f"({i(row['candidate_alerts']):,} alerts)"
            )

        if "capacity_rejected" in adaptive_windows.columns:
            row = adaptive_windows.loc[
                adaptive_windows["capacity_rejected"].idxmax()
            ]
            rejected_peak_text = (
                f"Monitoring Window {i(row['window'])} "
                f"({i(row['capacity_rejected']):,} rejected)"
            )

        if "frauds_missed" in adaptive_windows.columns:
            row = adaptive_windows.loc[
                adaptive_windows["frauds_missed"].idxmax()
            ]
            missed_peak_text = (
                f"Monitoring Window {i(row['window'])} "
                f"({i(row['frauds_missed']):,} missed frauds)"
            )

        if "operational_cost" in adaptive_windows.columns:
            row = adaptive_windows.loc[
                adaptive_windows["operational_cost"].idxmax()
            ]
            cost_peak_text = (
                f"Monitoring Window {i(row['window'])} "
                f"({money(row['operational_cost'])})"
            )

        monitored_columns = [
            column
            for column in [
                "candidate_alerts",
                "accepted_alerts",
                "capacity_rejected",
                "frauds_missed",
                "operational_cost",
            ]
            if column in adaptive_windows.columns
        ]

        variation_detected = any(
            trend_label(adaptive_windows[column]) != "Stable"
            for column in monitored_columns
        )

        stability_text = (
            "The replay showed meaningful variation across monitoring windows."
            if variation_detected
            else "The monitored outcomes remained broadly stable across the replay."
        )

        st.markdown(
            f"""
            <div class="decision-box">
                <strong>Overall monitoring conclusion</strong><br>
                Highest candidate workload: <strong>{candidate_peak_text}</strong>.<br>
                Largest budget overflow: <strong>{rejected_peak_text}</strong>.<br>
                Most missed fraud: <strong>{missed_peak_text}</strong>.<br>
                Highest operational cost: <strong>{cost_peak_text}</strong>.<br><br>
                {html.escape(stability_text)}
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
            "values": (1000.0, 3000.0, 10000.0, 50000.0),
            "display_values": "1,000 · 3,000 · 10,000 · 50,000 transactions",
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
            "purpose": "Tests how the minimum score required to enter the Adaptive risk zone affects workload and detection.",
        },
    }

    st.markdown("### Experiments included")
    experiment_names = list(experiment_definitions)
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
        "All experiments are now executed through one optimized API request. "
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
                sensitivity_payload = load_sensitivity_data(dict(params))
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

        st.markdown("### Executive findings")

        st.markdown(
            """
            <div class="info-box">
                <strong>Purpose of these checks</strong><br>
                Seven experiments were performed to see whether the decision layer still
                behaves clearly when its operating conditions change. In each experiment,
                only <strong>one parameter</strong> was modified and all other settings were
                kept unchanged. This allows the effect of each parameter to be examined
                separately.
            </div>
            """,
            unsafe_allow_html=True,
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
                "Experiments where Adaptive produced the stronger overall pattern.",
                "green",
            )

        with finding_kpi_3:
            metric_card(
                "Static performed best",
                f"{overview_static_families} / {len(experiment_names)}",
                "Experiments where Static produced the stronger overall pattern.",
                "orange",
            )

        with finding_kpi_4:
            metric_card(
                "No clear winner",
                f"{overview_tied_families}",
                "Experiments where neither policy won most tested settings.",
                "blue",
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

        st.markdown("### What was the overall result?")
        st.markdown(
            f"""
            <div class="takeaway">
                The <strong>Adaptive policy</strong> produced the stronger overall result in
                <strong>{overview_adaptive_families} of the {len(experiment_names)} experiments</strong>.
                The Static policy was stronger in <strong>{overview_static_families}</strong>
                experiment, while <strong>{overview_tied_families}</strong> experiment had no
                clear winner. This means Adaptive performed better more often, but it was not
                the best option under every tested configuration.
            </div>
            """,
            unsafe_allow_html=True,
        )

        difference_col, difference_text_col = st.columns([1, 2.25])

        with difference_col:
            metric_card(
                "Largest recall difference",
                f"{largest_gap_value:.2%}",
                largest_gap_experiment,
                "orange",
            )

        with difference_text_col:
            threshold_detail = (
                f" at a tested value of {largest_gap_setting:g}"
                if largest_gap_setting is not None
                else ""
            )
            st.markdown(
                f"""
                <div class="warning">
                    <strong>Where was the largest difference observed?</strong><br>
                    The largest difference between the two policies appeared during the
                    <strong>{html.escape(largest_gap_experiment)}</strong> experiment
                    {html.escape(threshold_detail)}. Their fraud recall differed by
                    <strong>{largest_gap_value:.2%}</strong>, meaning one policy detected that
                    much more of the known fraud than the other under this setting.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### What does this mean?")
        st.markdown(
            f"""
            <div class="takeaway">
                Overall, the decision layer responded in a consistent and understandable way
                when its operating settings changed. The Adaptive policy was generally the
                stronger option across the tested experiments, but the results also show that
                no policy is automatically best under every possible configuration. The purpose
                of these checks is therefore to demonstrate predictable behaviour, not to claim
                universal superiority.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("## Detailed experiment results")

        st.markdown("### What did each experiment show?")
        summary_rows = []
        all_frames = []
        for experiment_name, definition in experiment_definitions.items():
            frame = pd.DataFrame(result_map[experiment_name])
            all_frames.append(frame)
            summary_rows.append(
                {
                    "Experiment": experiment_name,
                    "Values tested": definition["display_values"],
                    "Main finding": build_plain_finding(frame),
                }
            )

        st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)

        combined_results = pd.concat(all_frames, ignore_index=True)
        total_adaptive = int((combined_results["winner"] == "Adaptive").sum())
        total_static = int((combined_results["winner"] == "Static").sum())
        total_ties = int((combined_results["winner"] == "Tie").sum())
        total_settings = len(combined_results)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Settings tested", f"{total_settings}", "One parameter changed at a time.", "blue")
        with c2:
            metric_card("Adaptive preferable", f"{total_adaptive}", "Higher recall, or lower cost when recall tied.", "green")
        with c3:
            metric_card("Static preferable", f"{total_static}", "Higher recall, or lower cost when recall tied.", "orange")
        with c4:
            metric_card("Equivalent result", f"{total_ties}", "Same recall and effectively equal cost.", "blue")

        st.markdown("### Explore one experiment")
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
                "static_cost": "Static operational cost",
                "adaptive_cost": "Adaptive operational cost",
                "adaptive_cost_saving": "Adaptive cost saving",
                "winner": "Preferred policy",
            }
        )
        st.dataframe(detail_display, width="stretch", hide_index=True)

        st.markdown(
            f"""
            <div class="chart-conclusion">
                <strong>Plain-language interpretation</strong><br>
                {html.escape(build_plain_finding(selected_frame))}
                A policy is marked as preferable when it detects a larger share of fraud.
                When recall is equal, the policy with the lower operational cost is preferred.
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