from __future__ import annotations

import html
from typing import Any

import pandas as pd
import requests
import streamlit as st


# =========================================================
# PART 1 OF 3
# CONFIGURATION, DESIGN, HELPERS, API, SIDEBAR,
# EXECUTIVE SUMMARY AND HOW THE SIMULATION WORKS
# =========================================================

API_BASE_URL = "http://127.0.0.1:8002"
SIMULATION_ENDPOINT = "simulation/sequential"

st.set_page_config(
    page_title="Fraud Decision Simulation Dashboard",
    page_icon="🛡️",
    layout="wide",
)


# =========================================================
# VISUAL DESIGN
# =========================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 3rem;
            max-width: 1550px;
        }

        .hero {
            padding: 1.45rem 1.6rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 16px;
            background: linear-gradient(
                135deg,
                rgba(30, 136, 229, 0.16),
                rgba(46, 125, 50, 0.08)
            );
        }

        .hero h1 {
            margin: 0 0 0.4rem 0;
            font-size: 2.15rem;
        }

        .hero p {
            margin: 0;
            font-size: 1rem;
            line-height: 1.55;
            color: rgba(230, 230, 230, 0.78);
        }

        .section-intro {
            padding: 1rem 1.1rem;
            margin: 0.45rem 0 1rem 0;
            border-left: 4px solid #1976d2;
            border-radius: 10px;
            background: rgba(25, 118, 210, 0.09);
            line-height: 1.55;
        }

        .learning-card {
            min-height: 185px;
            padding: 1rem 1.05rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 14px;
            background: rgba(128, 128, 128, 0.045);
        }

        .learning-card h3 {
            margin: 0 0 0.55rem 0;
            font-size: 1.02rem;
        }

        .learning-card p {
            margin: 0.25rem 0;
            line-height: 1.5;
            color: rgba(230, 230, 230, 0.78);
        }

        .metric-card {
            min-height: 160px;
            padding: 1rem 1.05rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 14px;
            background: rgba(128, 128, 128, 0.045);
        }

        .metric-card h3 {
            margin: 0;
            font-size: 0.98rem;
        }

        .metric-card .value {
            margin: 0.48rem 0 0.35rem 0;
            font-size: 1.78rem;
            font-weight: 700;
        }

        .metric-card .explanation {
            font-size: 0.88rem;
            line-height: 1.42;
            color: rgba(230, 230, 230, 0.72);
        }

        .tone-positive {
            border-top: 4px solid #2e7d32;
        }

        .tone-neutral {
            border-top: 4px solid #ef6c00;
        }

        .tone-negative {
            border-top: 4px solid #c62828;
        }

        .tone-information {
            border-top: 4px solid #1976d2;
        }

        .decision-card {
            padding: 1rem 1.1rem;
            border: 1px solid rgba(30, 136, 229, 0.42);
            border-radius: 13px;
            background: rgba(30, 136, 229, 0.09);
            line-height: 1.55;
        }

        .takeaway-card {
            padding: 1rem 1.1rem;
            border-left: 5px solid #2e7d32;
            border-radius: 12px;
            background: rgba(46, 125, 50, 0.10);
            line-height: 1.55;
        }

        .warning-card {
            padding: 1rem 1.1rem;
            border-left: 5px solid #ef6c00;
            border-radius: 12px;
            background: rgba(239, 108, 0, 0.10);
            line-height: 1.55;
        }

        .workflow-box {
            padding: 0.9rem 1rem;
            margin: 0.35rem 0;
            border: 1px solid rgba(128, 128, 128, 0.24);
            border-radius: 12px;
            text-align: center;
            background: rgba(128, 128, 128, 0.045);
        }

        .workflow-arrow {
            text-align: center;
            font-size: 1.4rem;
            opacity: 0.75;
            margin: 0.1rem 0;
        }

        .term-table td:first-child {
            font-weight: 700;
        }

        .footer-note {
            color: rgba(220, 220, 220, 0.62);
            font-size: 0.83rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# GENERIC HELPERS
# =========================================================

def safe_number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any) -> int:
    return int(round(safe_number(value)))


def money(value: Any) -> str:
    return f"€{safe_number(value):,.2f}"


def percentage(value: Any, decimals: int = 1) -> str:
    return f"{safe_number(value):.{decimals}%}"


def metric_card(
    title: str,
    value: str,
    explanation: str,
    icon: str,
    tone: str = "information",
) -> None:
    st.markdown(
        f"""
        <div class="metric-card tone-{tone}">
            <h3>{icon} {html.escape(title)}</h3>
            <div class="value">{html.escape(value)}</div>
            <div class="explanation">{html.escape(explanation)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def learning_card(
    title: str,
    explanation: str,
    why_it_matters: str,
    icon: str,
) -> None:
    st.markdown(
        f"""
        <div class="learning-card">
            <h3>{icon} {html.escape(title)}</h3>
            <p>{html.escape(explanation)}</p>
            <p><strong>Why it matters:</strong> {html.escape(why_it_matters)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_intro(question: str, explanation: str) -> None:
    st.markdown(
        f"""
        <div class="section-intro">
            <strong>{html.escape(question)}</strong><br>
            {html.escape(explanation)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def research_takeaway(title: str, explanation: str) -> None:
    st.markdown(
        f"""
        <div class="takeaway-card">
            <strong>{html.escape(title)}</strong><br>
            {html.escape(explanation)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def warning_explanation(title: str, explanation: str) -> None:
    st.markdown(
        f"""
        <div class="warning-card">
            <strong>{html.escape(title)}</strong><br>
            {html.escape(explanation)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_step(title: str, explanation: str) -> None:
    st.markdown(
        f"""
        <div class="workflow-box">
            <strong>{html.escape(title)}</strong><br>
            <span>{html.escape(explanation)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_arrow() -> None:
    st.markdown(
        '<div class="workflow-arrow">↓</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# DATA HELPERS
# =========================================================

@st.cache_data(show_spinner=False, ttl=60)
def get_simulation_data(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{API_BASE_URL}/{SIMULATION_ENDPOINT}",
        params=params,
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def get_summary(
    simulation_data: dict[str, Any],
    scenario_key: str,
) -> dict[str, Any]:
    return (
        simulation_data
        .get(scenario_key, {})
        .get("summary", {})
    )


def build_scenario_frame(
    simulation_data: dict[str, Any],
) -> pd.DataFrame:
    scenario_rows = simulation_data.get(
        "scenario_comparison",
        [],
    )

    if scenario_rows:
        return pd.DataFrame(scenario_rows)

    fallback_rows: list[dict[str, Any]] = []

    scenario_definitions = [
        ("static_batch", "Static Batch", "static", "batch"),
        ("static_sequential", "Static Sequential", "static", "sequential"),
        ("adaptive_batch", "Adaptive Batch", "adaptive", "batch"),
        ("adaptive_sequential", "Adaptive Sequential", "adaptive", "sequential"),
    ]

    for key, label, policy, mode in scenario_definitions:
        fallback_rows.append(
            {
                "scenario": key,
                "scenario_label": label,
                "policy": policy,
                "evaluation_mode": mode,
                **get_summary(simulation_data, key),
            }
        )

    return pd.DataFrame(fallback_rows)


def prepare_display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    display_frame = frame.copy()

    display_frame = display_frame.rename(
        columns={
            "scenario": "Scenario",
            "scenario_label": "Scenario",
            "selected_alerts": "Alerts",
            "frauds_detected": "Frauds detected",
            "frauds_missed": "Frauds missed",
            "false_positives": "False positives",
            "precision": "Precision",
            "recall": "Recall",
            "total_operational_cost": "Operational cost",
        }
    )

    if "Scenario" in display_frame.columns:
        display_frame["Scenario"] = (
            display_frame["Scenario"]
            .astype(str)
            .replace(
                {
                    "static_batch": "Static Batch",
                    "static_sequential": "Static Sequential",
                    "adaptive_batch": "Adaptive Batch",
                    "adaptive_sequential": "Adaptive Sequential",
                }
            )
        )

    for column in ["Precision", "Recall"]:
        if column in display_frame.columns:
            display_frame[column] = display_frame[column].map(
                lambda value: f"{safe_number(value):.2%}"
            )

    if "Operational cost" in display_frame.columns:
        display_frame["Operational cost"] = (
            display_frame["Operational cost"]
            .map(lambda value: f"€{safe_number(value):,.2f}")
        )

    preferred_columns = [
        "Scenario",
        "Alerts",
        "Frauds detected",
        "Frauds missed",
        "False positives",
        "Precision",
        "Recall",
        "Operational cost",
    ]

    return display_frame[
        [
            column
            for column in preferred_columns
            if column in display_frame.columns
        ]
    ]


def normalise_monitoring_frame(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    result = frame.copy().rename(
        columns={
            "monitoring_window": "window_number",
            "selected_alerts": "alerts",
            "suppressed_alerts": "suppressed",
            "capacity_rejected_alerts": "capacity_rejected",
            "policy_candidate_alerts": "candidate_alerts",
            "total_operational_cost": "operational_cost",
        }
    )

    if "window_number" in result.columns:
        result = result.sort_values("window_number")

    return result


def scenario_value(
    frame: pd.DataFrame,
    scenario: str,
    metric: str,
) -> float:
    if frame.empty:
        return 0.0

    if "scenario" not in frame.columns:
        return 0.0

    rows = frame.loc[
        frame["scenario"].astype(str).eq(scenario)
    ]

    if rows.empty or metric not in rows.columns:
        return 0.0

    return safe_number(rows.iloc[0][metric])


# =========================================================
# PAGE HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🛡️ Fraud Decision Simulation Dashboard</h1>
        <p>
            An educational simulation of how fraud alerts move from model scores
            to operational investigation decisions. The dashboard compares static
            and adaptive alert policies under ideal batch evaluation and realistic
            sequential analyst-capacity constraints.
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
    "Change one parameter at a time and observe how the decision system responds."
)

transaction_limit = st.sidebar.selectbox(
    "Transactions evaluated",
    options=[1000, 3000, 10000, 50000],
    index=2,
    help=(
        "The number of scored transactions included in the experiment. "
        "A larger value provides a broader evaluation but may take longer."
    ),
)

investigation_cost = st.sidebar.number_input(
    "Cost per investigation",
    min_value=0.0,
    value=10.0,
    step=1.0,
    help=(
        "The operational cost assigned to every alert that an analyst reviews."
    ),
)

static_threshold = st.sidebar.slider(
    "Static fraud threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.01,
    help=(
        "The fixed fraud-score boundary used by the Static Batch policy."
    ),
)

budget_multiplier = st.sidebar.slider(
    "Adaptive alert budget multiplier",
    min_value=0.0,
    max_value=2.0,
    value=1.4,
    step=0.1,
    help=(
        "Controls how much larger the adaptive alert budget can become "
        "relative to the static baseline."
    ),
)

with st.sidebar.expander("Adaptive policy settings"):
    risk_zone_floor = st.slider(
        "Risk-zone floor",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.01,
        help=(
            "Minimum fraud score required for transactions considered "
            "inside the adaptive risk zone."
        ),
    )

    alert_rate_low = st.slider(
        "Low alert-rate boundary",
        min_value=0.0,
        max_value=1.0,
        value=0.03,
        step=0.01,
        help=(
            "Legacy compatibility parameter retained by the backend."
        ),
    )

    alert_rate_high = st.slider(
        "High alert-rate boundary",
        min_value=0.0,
        max_value=1.0,
        value=0.10,
        step=0.01,
        help=(
            "Legacy compatibility parameter retained by the backend."
        ),
    )

with st.sidebar.expander("Sequential operating settings"):
    alert_budget_per_step = st.number_input(
        "Alerts allowed per time step",
        min_value=1,
        max_value=5000,
        value=30,
        step=5,
        help=(
            "The maximum number of alerts analysts can accept during "
            "each chronological step."
        ),
    )

    suppression_window = st.number_input(
        "Repeat-alert cooldown",
        min_value=0,
        max_value=100,
        value=3,
        step=1,
        help=(
            "Repeated alerts for the same entity are suppressed during "
            "this number of subsequent steps."
        ),
    )

    monitoring_window_size = st.selectbox(
        "Transactions per monitoring window",
        options=[250, 500, 1000, 2500, 5000],
        index=2,
        help=(
            "The number of chronological transactions grouped into each "
            "monitoring period."
        ),
    )

if st.sidebar.button(
    "Refresh results",
    use_container_width=True,
):
    st.cache_data.clear()

st.sidebar.divider()

st.sidebar.markdown(
    """
    **How to experiment**

    1. Start with the default settings.  
    2. Change only one parameter.  
    3. Compare Batch and Sequential results.  
    4. Observe whether capacity or suppression limits performance.
    """
)

st.sidebar.caption(f"API: `{API_BASE_URL}`")


# =========================================================
# API REQUEST
# =========================================================

simulation_params = {
    "limit": int(transaction_limit),
    "investigation_cost": float(investigation_cost),
    "static_threshold": float(static_threshold),
    "ranking_policy": "risk_zone",
    "risk_zone_floor": float(risk_zone_floor),
    "alert_rate_low": float(alert_rate_low),
    "alert_rate_high": float(alert_rate_high),
    "budget_multiplier": float(budget_multiplier),
    "alert_budget_per_step": int(alert_budget_per_step),
    "suppression_window": int(suppression_window),
    "monitoring_window_size": int(monitoring_window_size),
}

try:
    with st.spinner(
        "Running static and adaptive batch and sequential scenarios..."
    ):
        simulation_data = get_simulation_data(
            simulation_params
        )

except requests.exceptions.ConnectionError:
    st.error(
        "FastAPI is not available. Start it in another terminal with:\n\n"
        "`py -m uvicorn app.api.main:app --reload --port 8002`"
    )
    st.stop()

except requests.exceptions.Timeout:
    st.error(
        "The API request timed out. Try a smaller transaction limit."
    )
    st.stop()

except requests.exceptions.HTTPError as error:
    st.error(
        "FastAPI returned an error. Check the API terminal for details."
    )

    response = error.response

    if response is not None:
        try:
            st.json(response.json())
        except ValueError:
            st.code(response.text)

    st.exception(error)
    st.stop()

except requests.exceptions.RequestException as error:
    st.error(
        "An unexpected API communication error occurred."
    )
    st.exception(error)
    st.stop()


# =========================================================
# PREPARE RESPONSE
# =========================================================

parameters = simulation_data.get("parameters", {})

static_batch_summary = get_summary(
    simulation_data,
    "static_batch",
)

static_sequential_summary = get_summary(
    simulation_data,
    "static_sequential",
)

adaptive_batch_summary = get_summary(
    simulation_data,
    "adaptive_batch",
)

adaptive_sequential_summary = get_summary(
    simulation_data,
    "adaptive_sequential",
)

scenario_df = build_scenario_frame(
    simulation_data
)

comparison_differences = simulation_data.get(
    "comparison_differences",
    {},
)

static_windows_df = normalise_monitoring_frame(
    pd.DataFrame(
        simulation_data
        .get("static_sequential", {})
        .get("monitoring_windows", [])
    )
)

adaptive_windows_df = normalise_monitoring_frame(
    pd.DataFrame(
        simulation_data
        .get("adaptive_sequential", {})
        .get("monitoring_windows", [])
    )
)


# =========================================================
# NAVIGATION
# =========================================================

(
    overview_tab,
    workflow_tab,
    comparison_tab,
    capacity_tab,
    queue_tab,
    monitoring_tab,
    interpretation_tab,
    technical_tab,
) = st.tabs(
    [
        "1. Executive Summary",
        "2. How It Works",
        "3. Four Scenarios",
        "4. Capacity Impact",
        "5. Analyst Queue",
        "6. Monitoring",
        "7. Research Interpretation",
        "8. Technical Details",
    ]
)


# =========================================================
# 1. EXECUTIVE SUMMARY
# =========================================================

with overview_tab:
    st.header("Executive Summary")

    section_intro(
        "What question does this dashboard answer?",
        (
            "It examines whether an adaptive and cost-aware alerting policy "
            "provides greater operational usefulness than a static-threshold "
            "baseline, and whether that advantage remains visible after realistic "
            "analyst-capacity and suppression constraints are introduced."
        ),
    )

    st.markdown("### First, understand the two types of evaluation")

    concept1, concept2 = st.columns(2)

    with concept1:
        learning_card(
            "Batch evaluation",
            (
                "The complete dataset is evaluated as one global set. "
                "The policy selects alerts without modelling the order in "
                "which transactions arrive."
            ),
            (
                "It measures the decision policy's theoretical detection "
                "potential under ideal operating conditions."
            ),
            "📦",
        )

    with concept2:
        learning_card(
            "Sequential evaluation",
            (
                "Transactions are replayed chronologically. Candidate alerts "
                "must pass suppression and compete for limited analyst capacity "
                "within each time step."
            ),
            (
                "It shows whether strong policy performance can be realised "
                "under realistic operational constraints."
            ),
            "⏱️",
        )

    static_batch_recall = safe_number(
        static_batch_summary.get("recall")
    )
    adaptive_batch_recall = safe_number(
        adaptive_batch_summary.get("recall")
    )
    static_sequential_recall = safe_number(
        static_sequential_summary.get("recall")
    )
    adaptive_sequential_recall = safe_number(
        adaptive_sequential_summary.get("recall")
    )

    static_batch_cost = safe_number(
        static_batch_summary.get("total_operational_cost")
    )
    adaptive_batch_cost = safe_number(
        adaptive_batch_summary.get("total_operational_cost")
    )
    static_sequential_cost = safe_number(
        static_sequential_summary.get("total_operational_cost")
    )
    adaptive_sequential_cost = safe_number(
        adaptive_sequential_summary.get("total_operational_cost")
    )

    batch_recall_gain = (
        adaptive_batch_recall
        - static_batch_recall
    )

    sequential_recall_gain = (
        adaptive_sequential_recall
        - static_sequential_recall
    )

    batch_cost_change = (
        adaptive_batch_cost
        - static_batch_cost
    )

    sequential_cost_change = (
        adaptive_sequential_cost
        - static_sequential_cost
    )

    st.markdown("### Key findings from the current settings")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        metric_card(
            "Adaptive Batch recall",
            percentage(adaptive_batch_recall),
            (
                f"{batch_recall_gain:+.1%} compared with Static Batch. "
                "This shows the policy-level improvement before capacity limits."
            ),
            "📈",
            "positive"
            if batch_recall_gain >= 0
            else "negative",
        )

    with kpi2:
        metric_card(
            "Adaptive Sequential recall",
            percentage(adaptive_sequential_recall),
            (
                f"{sequential_recall_gain:+.1%} compared with Static Sequential. "
                "This shows the remaining advantage after operational constraints."
            ),
            "⏱️",
            "positive"
            if sequential_recall_gain > 0
            else "neutral",
        )

    with kpi3:
        metric_card(
            "Adaptive Batch cost",
            money(adaptive_batch_cost),
            (
                f"{money(abs(batch_cost_change))} "
                f"{'higher' if batch_cost_change > 0 else 'lower'} "
                "than Static Batch."
            ),
            "💰",
            "positive"
            if batch_cost_change <= 0
            else "negative",
        )

    with kpi4:
        metric_card(
            "Adaptive Sequential cost",
            money(adaptive_sequential_cost),
            (
                f"{money(abs(sequential_cost_change))} "
                f"{'higher' if sequential_cost_change > 0 else 'lower'} "
                "than Static Sequential."
            ),
            "🧮",
            "positive"
            if sequential_cost_change < 0
            else "neutral",
        )

    st.markdown("### What do the main metrics mean?")

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        learning_card(
            "Recall",
            (
                "The percentage of all real fraudulent transactions that "
                "were successfully detected."
            ),
            (
                "Low recall means many frauds escape investigation, even if "
                "the reviewed alerts appear accurate."
            ),
            "🎯",
        )

    with metric2:
        learning_card(
            "Precision",
            (
                "The percentage of investigated alerts that were actually fraudulent."
            ),
            (
                "Higher precision reduces unnecessary analyst workload, but a "
                "very strict policy may improve precision while missing more fraud."
            ),
            "🔍",
        )

    with metric3:
        learning_card(
            "Operational cost",
            (
                "Investigation cost plus the financial value of fraudulent "
                "transactions that were not detected."
            ),
            (
                "It connects predictive performance with business consequences."
            ),
            "💶",
        )

    st.markdown("### Scenario summary")

    st.dataframe(
        prepare_display_frame(scenario_df),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### How should these results be interpreted?")

    interpretation_left, interpretation_right = st.columns(2)

    with interpretation_left:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>Finding 1 — Policy effect</h3>
                <p>
                    Adaptive Batch recall is
                    <strong>{adaptive_batch_recall:.1%}</strong>,
                    compared with
                    <strong>{static_batch_recall:.1%}</strong>
                    for Static Batch.
                </p>
                <p>
                    This is a recall difference of
                    <strong>{batch_recall_gain:+.1%}</strong>.
                    The batch comparison isolates the benefit of the adaptive
                    decision policy before analyst-capacity constraints are applied.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with interpretation_right:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>Finding 2 — Operational effect</h3>
                <p>
                    Adaptive Sequential recall is
                    <strong>{adaptive_sequential_recall:.1%}</strong>,
                    compared with
                    <strong>{static_sequential_recall:.1%}</strong>
                    for Static Sequential.
                </p>
                <p>
                    The remaining difference is
                    <strong>{sequential_recall_gain:+.1%}</strong>.
                    This reveals how much of the adaptive advantage survives after
                    chronological capacity and suppression are introduced.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if abs(sequential_recall_gain) < 1e-9:
        warning_explanation(
            "Why are the Sequential results identical?",
            (
                "Both policies are constrained by the same maximum analyst capacity. "
                "When capacity is very low, the accepted alerts may be the same "
                "highest-priority cases under both policies. The adaptive policy "
                "still generates more candidates, but the additional candidates "
                "cannot enter the investigation queue."
            ),
        )
    elif sequential_recall_gain > 0:
        research_takeaway(
            "Current research takeaway",
            (
                "The adaptive policy retains part of its batch advantage after "
                "realistic operating constraints are introduced. This indicates "
                "that sufficient analyst capacity allows the decision layer to "
                "convert better candidate selection into better detection."
            ),
        )
    else:
        warning_explanation(
            "Current research takeaway",
            (
                "Under the selected operating settings, the adaptive policy does "
                "not outperform the static baseline sequentially. This suggests "
                "that operational constraints or ranking behaviour require closer "
                "inspection."
            ),
        )


# =========================================================
# 2. HOW THE SIMULATION WORKS
# =========================================================

with workflow_tab:
    st.header("How the Simulation Works")

    section_intro(
        "Why is the simulation separated into stages?",
        (
            "A fraud model does not make the final operational decision by itself. "
            "The simulation separates prediction, policy selection, chronological "
            "replay, suppression, analyst capacity and evaluation so that the "
            "effect of each component can be studied independently."
        ),
    )

    st.markdown("### End-to-end decision workflow")

    workflow_step(
        "1. Scored transactions",
        (
            "Each transaction already has a fraud score generated by the "
            "machine-learning model."
        ),
    )
    workflow_arrow()

    workflow_step(
        "2. Static or Adaptive decision policy",
        (
            "The policy decides which scored transactions become candidate alerts."
        ),
    )
    workflow_arrow()

    workflow_step(
        "3. Candidate alerts",
        (
            "These alerts represent the policy's proposed investigation workload."
        ),
    )
    workflow_arrow()

    workflow_step(
        "4. Chronological replay",
        (
            "Candidate alerts are processed according to the time step in which "
            "their transactions occurred."
        ),
    )
    workflow_arrow()

    workflow_step(
        "5. Suppression check",
        (
            "Repeated alerts for the same entity can be removed during the "
            "configured cooldown period."
        ),
    )
    workflow_arrow()

    workflow_step(
        "6. Analyst-capacity check",
        (
            "Only the highest-priority remaining alerts can be accepted until "
            "the per-step investigation limit is reached."
        ),
    )
    workflow_arrow()

    workflow_step(
        "7. Evaluation",
        (
            "Accepted alerts are compared with ground truth to calculate recall, "
            "precision, missed-fraud cost and total operational cost."
        ),
    )

    st.markdown("### What is the difference between the two policies?")

    policy1, policy2 = st.columns(2)

    with policy1:
        learning_card(
            "Static policy",
            (
                "Uses a fixed fraud-score threshold. Every transaction above "
                "the same threshold becomes a candidate alert."
            ),
            (
                "It provides a transparent baseline, but it cannot respond to "
                "changes in alert volume, workload or operational value."
            ),
            "📏",
        )

    with policy2:
        learning_card(
            "Adaptive policy",
            (
                "Uses the validated risk-zone and budget-aware decision logic "
                "to prioritise a broader set of operationally useful candidates."
            ),
            (
                "It can increase fraud coverage, but its benefit still depends "
                "on whether analysts have enough capacity to review the extra alerts."
            ),
            "🧠",
        )

    st.markdown("### What happens inside each chronological step?")

    step1, step2, step3, step4 = st.columns(4)

    with step1:
        learning_card(
            "Candidate ranking",
            (
                "Candidate alerts are ordered by rank score and fraud score "
                "within the current step."
            ),
            (
                "The highest-priority cases are considered first."
            ),
            "1️⃣",
        )

    with step2:
        learning_card(
            "Suppression",
            (
                "Repeated alerts for the same entity may be removed before "
                "capacity is consumed."
            ),
            (
                "This reduces duplicate workload and alert fatigue."
            ),
            "2️⃣",
        )

    with step3:
        learning_card(
            "Capacity allocation",
            (
                "The remaining alerts are accepted until the analyst limit "
                "for that step is full."
            ),
            (
                "Alerts outside capacity are not necessarily poor alerts; "
                "they are operationally unreviewable."
            ),
            "3️⃣",
        )

    with step4:
        learning_card(
            "Outcome evaluation",
            (
                "The accepted investigations are compared with the real fraud labels."
            ),
            (
                "This distinguishes policy quality from operational feasibility."
            ),
            "4️⃣",
        )

    st.markdown("### Current operating configuration")

    cfg1, cfg2, cfg3, cfg4 = st.columns(4)

    with cfg1:
        metric_card(
            "Chronological steps",
            f"{as_int(parameters.get('unique_steps')):,}",
            (
                "Distinct time steps across which transactions and alerts are replayed."
            ),
            "🕒",
        )

    with cfg2:
        metric_card(
            "Capacity per step",
            f"{as_int(parameters.get('alert_budget_per_step')):,}",
            (
                "Maximum number of alerts that analysts can accept during each step."
            ),
            "👥",
            "neutral",
        )

    with cfg3:
        metric_card(
            "Maximum sequential capacity",
            f"{as_int(parameters.get('maximum_sequential_capacity')):,}",
            (
                "Theoretical total capacity: time steps multiplied by capacity per step."
            ),
            "📦",
            "neutral",
        )

    with cfg4:
        metric_card(
            "Suppression window",
            f"{as_int(parameters.get('suppression_window')):,} steps",
            (
                "Number of steps during which repeated alerts for the same entity "
                "are suppressed."
            ),
            "🔁",
        )

    st.markdown("### Example of the capacity mechanism")

    total_capacity = as_int(
        parameters.get("maximum_sequential_capacity")
    )
    adaptive_candidates = as_int(
        adaptive_sequential_summary.get(
            "policy_candidate_alerts"
        )
    )
    adaptive_selected = as_int(
        adaptive_sequential_summary.get(
            "selected_alerts"
        )
    )
    adaptive_suppressed = as_int(
        adaptive_sequential_summary.get(
            "suppressed_alerts"
        )
    )
    adaptive_rejected = as_int(
        adaptive_sequential_summary.get(
            "capacity_rejected_alerts"
        )
    )

    st.markdown(
        f"""
        <div class="decision-card">
            <h3>Adaptive Sequential workflow under the current settings</h3>
            <p>
                The adaptive policy generated
                <strong>{adaptive_candidates:,}</strong> candidate alerts.
            </p>
            <p>
                The simulation had a theoretical maximum capacity of
                <strong>{total_capacity:,}</strong> investigations.
            </p>
            <p>
                It accepted <strong>{adaptive_selected:,}</strong> alerts,
                suppressed <strong>{adaptive_suppressed:,}</strong> repeated alerts
                and rejected <strong>{adaptive_rejected:,}</strong> alerts because
                the available capacity had already been exhausted.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    research_takeaway(
        "Educational takeaway",
        (
            "The machine-learning model identifies risk, but the decision layer "
            "and operational environment determine which risks are actually reviewed. "
            "A strong model cannot prevent fraud if its alerts cannot reach an analyst."
        ),
    )


# =========================================================
# PART 2 OF 3
# FOUR-SCENARIO COMPARISON, CAPACITY IMPACT,
# AND ANALYST QUEUE
# =========================================================


# =========================================================
# 3. FOUR-SCENARIO COMPARISON
# =========================================================

with comparison_tab:
    st.header("Four-Scenario Comparison")

    section_intro(
        "Why are four scenarios necessary?",
        (
            "The experiment uses two decision policies and two evaluation modes. "
            "This creates four scenarios that separate policy quality from "
            "operational feasibility. Without this separation, a strong decision "
            "policy could appear weak simply because analyst capacity is limited."
        ),
    )

    st.markdown("### The four scenarios at a glance")

    scenario1, scenario2 = st.columns(2)

    with scenario1:
        learning_card(
            "Static Batch",
            (
                "A fixed fraud-score threshold is applied to the complete dataset "
                "without chronological capacity or suppression."
            ),
            (
                "It provides the baseline policy result under ideal operating conditions."
            ),
            "1️⃣",
        )

    with scenario2:
        learning_card(
            "Adaptive Batch",
            (
                "The validated adaptive decision layer selects and ranks alerts "
                "using the risk-zone and budget-aware policy."
            ),
            (
                "It shows whether the adaptive policy improves fraud coverage and "
                "business cost before operational restrictions are applied."
            ),
            "2️⃣",
        )

    scenario3, scenario4 = st.columns(2)

    with scenario3:
        learning_card(
            "Static Sequential",
            (
                "Static-policy alerts are replayed chronologically and must pass "
                "suppression and analyst-capacity checks."
            ),
            (
                "It measures the operational performance of the static baseline."
            ),
            "3️⃣",
        )

    with scenario4:
        learning_card(
            "Adaptive Sequential",
            (
                "Adaptive-policy alerts are replayed under the same chronological "
                "capacity and suppression rules."
            ),
            (
                "It reveals whether the adaptive policy's batch advantage survives "
                "in a realistic investigation environment."
            ),
            "4️⃣",
        )

    st.markdown("### Why should Batch and Sequential results not be mixed?")

    batch_seq_left, batch_seq_right = st.columns(2)

    with batch_seq_left:
        st.markdown(
            """
            <div class="decision-card">
                <h3>Batch answers a policy question</h3>
                <p>
                    If the organisation could review every alert proposed by the
                    policy, how many frauds would be detected and what would the
                    operational cost be?
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with batch_seq_right:
        st.markdown(
            """
            <div class="decision-card">
                <h3>Sequential answers an operations question</h3>
                <p>
                    Once alerts arrive over time and analysts have limited capacity,
                    how much of the policy's theoretical benefit can actually be realised?
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Current scenario results")

    scenario_display_df = prepare_display_frame(
        scenario_df
    )

    st.dataframe(
        scenario_display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### How to read this table")

    read1, read2, read3, read4 = st.columns(4)

    with read1:
        learning_card(
            "Alerts",
            (
                "The number of transactions selected for investigation in the scenario."
            ),
            (
                "More alerts may improve recall, but they also increase workload "
                "and investigation cost."
            ),
            "🚨",
        )

    with read2:
        learning_card(
            "Frauds detected",
            (
                "The number of actual fraudulent transactions included among "
                "the accepted alerts."
            ),
            (
                "This is the direct fraud-capture outcome."
            ),
            "✅",
        )

    with read3:
        learning_card(
            "Frauds missed",
            (
                "Actual fraudulent transactions that were not accepted for investigation."
            ),
            (
                "Missed fraud contributes directly to missed-fraud cost."
            ),
            "❌",
        )

    with read4:
        learning_card(
            "False positives",
            (
                "Legitimate transactions that were investigated as alerts."
            ),
            (
                "They consume analyst capacity without preventing fraud loss."
            ),
            "⚠️",
        )

    if not scenario_df.empty:
        chart_frame = scenario_df.copy()

        if "scenario" in chart_frame.columns:
            chart_frame["Scenario"] = (
                chart_frame["scenario"]
                .astype(str)
                .replace(
                    {
                        "static_batch": "Static Batch",
                        "static_sequential": "Static Sequential",
                        "adaptive_batch": "Adaptive Batch",
                        "adaptive_sequential": "Adaptive Sequential",
                    }
                )
            )

        st.markdown("### Visual comparison")

        chart1, chart2 = st.columns(2)

        with chart1:
            st.markdown("#### Fraud detection outcomes")

            fraud_chart_columns = [
                column
                for column in [
                    "Scenario",
                    "frauds_detected",
                    "frauds_missed",
                ]
                if column in chart_frame.columns
            ]

            if len(fraud_chart_columns) >= 2:
                st.bar_chart(
                    chart_frame[
                        fraud_chart_columns
                    ].set_index("Scenario"),
                    use_container_width=True,
                )

            st.caption(
                "Interpretation: a stronger scenario detects more frauds and leaves "
                "fewer frauds outside investigation."
            )

        with chart2:
            st.markdown("#### Alert volume")

            if {
                "Scenario",
                "selected_alerts",
            }.issubset(chart_frame.columns):
                st.bar_chart(
                    chart_frame[
                        [
                            "Scenario",
                            "selected_alerts",
                        ]
                    ].set_index("Scenario"),
                    use_container_width=True,
                )

            st.caption(
                "Interpretation: alert volume represents workload, not only detection."
            )

        chart3, chart4 = st.columns(2)

        with chart3:
            st.markdown("#### Recall and precision")

            performance_columns = [
                column
                for column in [
                    "Scenario",
                    "recall",
                    "precision",
                ]
                if column in chart_frame.columns
            ]

            if len(performance_columns) >= 2:
                st.bar_chart(
                    chart_frame[
                        performance_columns
                    ].set_index("Scenario"),
                    use_container_width=True,
                )

            st.caption(
                "Recall measures fraud coverage. Precision measures how many reviewed "
                "alerts were truly fraudulent."
            )

        with chart4:
            st.markdown("#### Total operational cost")

            if {
                "Scenario",
                "total_operational_cost",
            }.issubset(chart_frame.columns):
                st.bar_chart(
                    chart_frame[
                        [
                            "Scenario",
                            "total_operational_cost",
                        ]
                    ].set_index("Scenario"),
                    use_container_width=True,
                )

            st.caption(
                "Lower cost indicates a better balance between investigation workload "
                "and missed fraud loss."
            )

    st.markdown("### Difference analysis")

    section_intro(
        "What does a difference value mean?",
        (
            "Each row compares a starting scenario with an ending scenario. "
            "Positive recall differences indicate improved fraud coverage. "
            "Negative operational-cost differences indicate cost savings."
        ),
    )

    difference_labels = {
        "static_batch_to_static_sequential":
            "Static Batch → Static Sequential",
        "adaptive_batch_to_adaptive_sequential":
            "Adaptive Batch → Adaptive Sequential",
        "static_batch_to_adaptive_batch":
            "Static Batch → Adaptive Batch",
        "static_sequential_to_adaptive_sequential":
            "Static Sequential → Adaptive Sequential",
    }

    difference_rows: list[dict[str, Any]] = []

    for key, label in difference_labels.items():
        values = comparison_differences.get(key, {})

        difference_rows.append(
            {
                "Comparison": label,
                "Alert difference": as_int(
                    values.get("alert_difference")
                ),
                "Frauds detected difference": as_int(
                    values.get("frauds_detected_difference")
                ),
                "Frauds missed difference": as_int(
                    values.get("frauds_missed_difference")
                ),
                "Recall difference": safe_number(
                    values.get("recall_difference")
                ),
                "Precision difference": safe_number(
                    values.get("precision_difference")
                ),
                "Operational cost difference": safe_number(
                    values.get("operational_cost_difference")
                ),
            }
        )

    difference_df = pd.DataFrame(
        difference_rows
    )

    display_difference_df = difference_df.copy()

    display_difference_df["Recall difference"] = (
        display_difference_df["Recall difference"]
        .map(lambda value: f"{value:+.2%}")
    )

    display_difference_df["Precision difference"] = (
        display_difference_df["Precision difference"]
        .map(lambda value: f"{value:+.2%}")
    )

    display_difference_df["Operational cost difference"] = (
        display_difference_df["Operational cost difference"]
        .map(lambda value: f"€{value:+,.2f}")
    )

    st.dataframe(
        display_difference_df,
        use_container_width=True,
        hide_index=True,
    )

    static_batch_frauds = as_int(
        static_batch_summary.get("frauds_detected")
    )
    adaptive_batch_frauds = as_int(
        adaptive_batch_summary.get("frauds_detected")
    )
    static_seq_frauds = as_int(
        static_sequential_summary.get("frauds_detected")
    )
    adaptive_seq_frauds = as_int(
        adaptive_sequential_summary.get("frauds_detected")
    )

    batch_extra_frauds = (
        adaptive_batch_frauds
        - static_batch_frauds
    )

    sequential_extra_frauds = (
        adaptive_seq_frauds
        - static_seq_frauds
    )

    result_left, result_right = st.columns(2)

    with result_left:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>Batch interpretation</h3>
                <p>
                    Adaptive Batch detected
                    <strong>{batch_extra_frauds:+,}</strong>
                    additional fraud cases compared with Static Batch.
                </p>
                <p>
                    This comparison represents the direct contribution of the
                    adaptive decision policy.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with result_right:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>Sequential interpretation</h3>
                <p>
                    Adaptive Sequential detected
                    <strong>{sequential_extra_frauds:+,}</strong>
                    additional fraud cases compared with Static Sequential.
                </p>
                <p>
                    This comparison represents the policy advantage that remains
                    after capacity and suppression are applied.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    research_takeaway(
        "Research takeaway",
        (
            "The four-scenario design prevents operational constraints from being "
            "mistaken for policy failure. Batch scenarios evaluate decision quality, "
            "while Sequential scenarios evaluate whether that quality can be delivered "
            "within a realistic investigation process."
        ),
    )


# =========================================================
# 4. CAPACITY IMPACT
# =========================================================

with capacity_tab:
    st.header("Capacity and Sequential Effects")

    section_intro(
        "Why does analyst capacity matter?",
        (
            "Fraud systems can generate more alerts than analysts can investigate. "
            "The sequential simulation therefore limits accepted alerts within each "
            "time step. This converts analyst availability into an explicit component "
            "of system performance."
        ),
    )

    st.markdown("### Capacity is not the same as alert quality")

    quality1, quality2 = st.columns(2)

    with quality1:
        learning_card(
            "Policy candidate",
            (
                "An alert proposed by the Static or Adaptive decision policy."
            ),
            (
                "It indicates that the policy considered the transaction worthy "
                "of investigation."
            ),
            "🎯",
        )

    with quality2:
        learning_card(
            "Capacity-rejected alert",
            (
                "A valid candidate alert that could not be accepted because the "
                "analyst limit for its time step was already full."
            ),
            (
                "Rejection does not mean the alert was low quality or incorrect."
            ),
            "⛔",
        )

    st.markdown("### The capacity workflow")

    workflow_step(
        "Policy candidate alerts",
        (
            "The Static or Adaptive policy proposes a set of alerts."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Suppression check",
        (
            "Repeated entity alerts inside the cooldown window are removed."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Priority ordering",
        (
            "Remaining candidates are ordered by rank score and fraud score "
            "within the current step."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Capacity allocation",
        (
            "The highest-priority alerts are accepted until the analyst limit is full."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Overflow",
        (
            "Remaining candidates are marked as capacity rejected and are not investigated."
        ),
    )

    max_capacity = as_int(
        parameters.get("maximum_sequential_capacity")
    )

    capacity_per_step = as_int(
        parameters.get("alert_budget_per_step")
    )

    unique_steps = as_int(
        parameters.get("unique_steps")
    )

    static_candidates = as_int(
        static_sequential_summary.get(
            "policy_candidate_alerts"
        )
    )
    adaptive_candidates = as_int(
        adaptive_sequential_summary.get(
            "policy_candidate_alerts"
        )
    )

    static_selected = as_int(
        static_sequential_summary.get(
            "selected_alerts"
        )
    )
    adaptive_selected = as_int(
        adaptive_sequential_summary.get(
            "selected_alerts"
        )
    )

    static_suppressed = as_int(
        static_sequential_summary.get(
            "suppressed_alerts"
        )
    )
    adaptive_suppressed = as_int(
        adaptive_sequential_summary.get(
            "suppressed_alerts"
        )
    )

    static_rejected = as_int(
        static_sequential_summary.get(
            "capacity_rejected_alerts"
        )
    )
    adaptive_rejected = as_int(
        adaptive_sequential_summary.get(
            "capacity_rejected_alerts"
        )
    )

    st.markdown("### Current capacity configuration")

    cap1, cap2, cap3, cap4 = st.columns(4)

    with cap1:
        metric_card(
            "Time steps",
            f"{unique_steps:,}",
            (
                "Number of chronological periods in which separate capacity "
                "limits are applied."
            ),
            "🕒",
        )

    with cap2:
        metric_card(
            "Capacity per step",
            f"{capacity_per_step:,}",
            (
                "Maximum accepted alerts during one chronological step."
            ),
            "👥",
            "neutral",
        )

    with cap3:
        metric_card(
            "Maximum total capacity",
            f"{max_capacity:,}",
            (
                "Theoretical total capacity across all time steps."
            ),
            "📦",
            "neutral",
        )

    with cap4:
        metric_card(
            "Adaptive overflow",
            f"{adaptive_rejected:,}",
            (
                "Adaptive candidate alerts rejected because capacity was exhausted."
            ),
            "⛔",
            "negative",
        )

    st.markdown("### Static and Adaptive capacity accounting")

    capacity_df = pd.DataFrame(
        [
            {
                "Scenario": "Static Sequential",
                "Candidate alerts": static_candidates,
                "Accepted alerts": static_selected,
                "Suppressed alerts": static_suppressed,
                "Capacity rejected": static_rejected,
                "Acceptance rate": (
                    static_selected / static_candidates
                    if static_candidates
                    else 0.0
                ),
                "Capacity-rejection rate": (
                    static_rejected / static_candidates
                    if static_candidates
                    else 0.0
                ),
            },
            {
                "Scenario": "Adaptive Sequential",
                "Candidate alerts": adaptive_candidates,
                "Accepted alerts": adaptive_selected,
                "Suppressed alerts": adaptive_suppressed,
                "Capacity rejected": adaptive_rejected,
                "Acceptance rate": (
                    adaptive_selected / adaptive_candidates
                    if adaptive_candidates
                    else 0.0
                ),
                "Capacity-rejection rate": (
                    adaptive_rejected / adaptive_candidates
                    if adaptive_candidates
                    else 0.0
                ),
            },
        ]
    )

    capacity_chart = (
        capacity_df
        .set_index("Scenario")[
            [
                "Accepted alerts",
                "Suppressed alerts",
                "Capacity rejected",
            ]
        ]
    )

    st.bar_chart(
        capacity_chart,
        use_container_width=True,
    )

    capacity_display_df = capacity_df.copy()

    capacity_display_df["Acceptance rate"] = (
        capacity_display_df["Acceptance rate"]
        .map(lambda value: f"{value:.2%}")
    )

    capacity_display_df["Capacity-rejection rate"] = (
        capacity_display_df["Capacity-rejection rate"]
        .map(lambda value: f"{value:.2%}")
    )

    st.dataframe(
        capacity_display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### What does the current configuration mean in practice?")

    practical_left, practical_right = st.columns(2)

    with practical_left:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>Static Sequential</h3>
                <p>
                    The static policy proposed
                    <strong>{static_candidates:,}</strong> candidate alerts.
                </p>
                <p>
                    The sequential engine accepted
                    <strong>{static_selected:,}</strong>,
                    suppressed <strong>{static_suppressed:,}</strong>
                    and rejected <strong>{static_rejected:,}</strong>
                    because of capacity.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with practical_right:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>Adaptive Sequential</h3>
                <p>
                    The adaptive policy proposed
                    <strong>{adaptive_candidates:,}</strong> candidate alerts.
                </p>
                <p>
                    The sequential engine accepted
                    <strong>{adaptive_selected:,}</strong>,
                    suppressed <strong>{adaptive_suppressed:,}</strong>
                    and rejected <strong>{adaptive_rejected:,}</strong>
                    because of capacity.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    static_seq_recall = safe_number(
        static_sequential_summary.get("recall")
    )
    adaptive_seq_recall = safe_number(
        adaptive_sequential_summary.get("recall")
    )

    sequential_gain = (
        adaptive_seq_recall
        - static_seq_recall
    )

    st.markdown("### How does capacity affect the policy comparison?")

    if abs(sequential_gain) < 1e-9:
        warning_explanation(
            "Severe-capacity result",
            (
                "The Static and Adaptive Sequential scenarios currently achieve "
                "the same recall. The shared capacity limit is sufficiently restrictive "
                "that both policies end up accepting essentially the same highest-priority "
                "alerts. The additional Adaptive candidates remain outside capacity."
            ),
        )
    elif sequential_gain > 0:
        research_takeaway(
            "Capacity-sensitive advantage",
            (
                f"Adaptive Sequential recall is {sequential_gain:+.1%} higher than "
                "Static Sequential recall. The selected capacity is large enough for "
                "part of the Adaptive policy's superior candidate set to reach analysts."
            ),
        )
    else:
        warning_explanation(
            "Unexpected capacity result",
            (
                f"Adaptive Sequential recall is {abs(sequential_gain):.1%} lower than "
                "Static Sequential recall under the selected settings. This should be "
                "investigated through step-level monitoring and queue-level ranking."
            ),
        )

    st.markdown("### Suggested capacity experiment")

    section_intro(
        "How can capacity sensitivity be tested?",
        (
            "Change only the 'Alerts allowed per time step' setting and record "
            "Static Sequential recall, Adaptive Sequential recall and operational cost. "
            "This reveals the capacity level at which the Adaptive policy begins to "
            "convert its batch advantage into operational improvement."
        ),
    )

    experiment_df = pd.DataFrame(
        [
            {
                "Capacity per step": 20,
                "Static Sequential recall": "Run experiment",
                "Adaptive Sequential recall": "Run experiment",
                "Interpretation": "Very severe capacity",
            },
            {
                "Capacity per step": 30,
                "Static Sequential recall": "Run experiment",
                "Adaptive Sequential recall": "Run experiment",
                "Interpretation": "Severe capacity",
            },
            {
                "Capacity per step": 40,
                "Static Sequential recall": "Run experiment",
                "Adaptive Sequential recall": "Run experiment",
                "Interpretation": "Transition region",
            },
            {
                "Capacity per step": 50,
                "Static Sequential recall": "Run experiment",
                "Adaptive Sequential recall": "Run experiment",
                "Interpretation": "Moderate capacity",
            },
            {
                "Capacity per step": 75,
                "Static Sequential recall": "Run experiment",
                "Adaptive Sequential recall": "Run experiment",
                "Interpretation": "Higher capacity",
            },
            {
                "Capacity per step": 100,
                "Static Sequential recall": "Run experiment",
                "Adaptive Sequential recall": "Run experiment",
                "Interpretation": "Near batch-scale capacity",
            },
        ]
    )

    st.dataframe(
        experiment_df,
        use_container_width=True,
        hide_index=True,
    )

    research_takeaway(
        "Capacity research takeaway",
        (
            "Analyst capacity is not a secondary implementation detail. "
            "It determines whether an improved decision policy can translate "
            "into improved fraud detection. Policy design and operational capacity "
            "must therefore be evaluated together."
        ),
    )


# =========================================================
# 5. ANALYST QUEUE
# =========================================================

with queue_tab:
    st.header("Analyst Queue")

    section_intro(
        "Why is an analyst queue necessary?",
        (
            "A fraud decision system may generate hundreds or thousands of alerts, "
            "but analysts require a manageable and prioritised list. The Analyst Queue "
            "connects model predictions and decision-policy rankings to the cases that "
            "human investigators actually review."
        ),
    )

    st.markdown("### From model score to analyst investigation")

    workflow_step(
        "Machine-learning model",
        (
            "Assigns a fraud score to each transaction."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Decision policy",
        (
            "Determines whether the transaction becomes an alert candidate."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Priority ranking",
        (
            "Uses rank score and policy logic to order candidate alerts."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Suppression and capacity",
        (
            "Removes repeated alerts and limits the number of accepted cases."
        ),
    )
    workflow_arrow()

    workflow_step(
        "Analyst Queue",
        (
            "Presents the accepted alerts in the order analysts should investigate them."
        ),
    )

    st.markdown("### Current Adaptive Sequential queue accounting")

    queue_candidates = as_int(
        adaptive_sequential_summary.get(
            "policy_candidate_alerts"
        )
    )
    queue_selected = as_int(
        adaptive_sequential_summary.get(
            "selected_alerts"
        )
    )
    queue_suppressed = as_int(
        adaptive_sequential_summary.get(
            "suppressed_alerts"
        )
    )
    queue_rejected = as_int(
        adaptive_sequential_summary.get(
            "capacity_rejected_alerts"
        )
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        metric_card(
            "Candidate alerts",
            f"{queue_candidates:,}",
            (
                "Transactions proposed by the Adaptive decision policy."
            ),
            "🚨",
            "neutral",
        )

    with q2:
        metric_card(
            "Accepted for review",
            f"{queue_selected:,}",
            (
                "Highest-priority alerts that entered the analyst workload."
            ),
            "👩‍💼",
            "positive",
        )

    with q3:
        metric_card(
            "Suppressed",
            f"{queue_suppressed:,}",
            (
                "Repeated entity alerts removed during the cooldown period."
            ),
            "🔁",
            "information",
        )

    with q4:
        metric_card(
            "Capacity overflow",
            f"{queue_rejected:,}",
            (
                "Valid candidate alerts that could not be investigated."
            ),
            "⏳",
            "negative",
        )

    st.markdown(
        f"""
        <div class="decision-card">
            <h3>Operational workflow</h3>
            <p>
                <strong>{queue_candidates:,}</strong> Adaptive candidate alerts
                were generated.
            </p>
            <p>
                <strong>{queue_selected:,}</strong> were accepted for analyst review,
                <strong>{queue_suppressed:,}</strong> were suppressed as repeated alerts,
                and <strong>{queue_rejected:,}</strong> remained outside the current
                analyst capacity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### What should each queue column mean?")

    column1, column2 = st.columns(2)

    with column1:
        learning_card(
            "Fraud score",
            (
                "Probability or risk estimate produced by the machine-learning model."
            ),
            (
                "It represents predictive risk, but it is not automatically the "
                "final investigation priority."
            ),
            "📊",
        )

        learning_card(
            "Rank score",
            (
                "Priority score used by the decision layer to order candidate alerts."
            ),
            (
                "It allows operational value and policy logic to influence the queue."
            ),
            "🏅",
        )

        learning_card(
            "Expected benefit",
            (
                "Estimated financial value of investigating the case."
            ),
            (
                "It connects fraud risk with potential loss prevention."
            ),
            "💷",
        )

    with column2:
        learning_card(
            "Queue position",
            (
                "The order in which the analyst should review the accepted alert."
            ),
            (
                "Cases at the top of the queue receive attention first."
            ),
            "📍",
        )

        learning_card(
            "Sequential decision",
            (
                "Operational outcome such as alert, suppressed, capacity_rejected "
                "or no_alert."
            ),
            (
                "It explains why a policy candidate did or did not reach an analyst."
            ),
            "🔀",
        )

        learning_card(
            "Severity",
            (
                "Human-readable urgency category such as Critical, High or Medium."
            ),
            (
                "It helps analysts interpret technical scores quickly."
            ),
            "🚩",
        )

    st.markdown("### Why is the real transaction table not shown yet?")

    warning_explanation(
        "Current backend limitation",
        (
            "The current simulation endpoint returns scenario summaries and monitoring "
            "windows, but it does not return the complete transaction-level Sequential "
            "DataFrame. Therefore, the dashboard can explain the queue and its aggregate "
            "accounting, but it cannot yet display real transaction rows."
        ),
    )

    st.markdown("### Required transaction-level queue fields")

    expected_queue_columns = pd.DataFrame(
        [
            {
                "Queue field": "transaction_id",
                "Operational meaning": "Unique transaction identifier",
                "Educational purpose": "Links the alert to the original transaction",
            },
            {
                "Queue field": "step",
                "Operational meaning": "Chronological simulation step",
                "Educational purpose": "Shows when the alert entered the workflow",
            },
            {
                "Queue field": "type",
                "Operational meaning": "Transaction category",
                "Educational purpose": "Supports operational filtering",
            },
            {
                "Queue field": "amount",
                "Operational meaning": "Transaction value",
                "Educational purpose": "Provides financial context",
            },
            {
                "Queue field": "fraud_score",
                "Operational meaning": "Model-assigned fraud risk",
                "Educational purpose": "Explains predictive risk",
            },
            {
                "Queue field": "rank_score",
                "Operational meaning": "Decision-layer priority",
                "Educational purpose": "Explains queue ordering",
            },
            {
                "Queue field": "candidate_priority_rank",
                "Operational meaning": "Rank within the current step",
                "Educational purpose": "Shows step-level prioritisation",
            },
            {
                "Queue field": "sequential_decision",
                "Operational meaning": "Final operational outcome",
                "Educational purpose": "Explains alert, suppression or rejection",
            },
            {
                "Queue field": "selected_alert",
                "Operational meaning": "Whether the analyst receives the case",
                "Educational purpose": "Separates candidates from accepted workload",
            },
            {
                "Queue field": "isFraud",
                "Operational meaning": "Ground-truth label",
                "Educational purpose": "Used only for retrospective evaluation",
            },
        ]
    )

    st.dataframe(
        expected_queue_columns,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### How the final queue should be used")

    use1, use2, use3 = st.columns(3)

    with use1:
        learning_card(
            "Operational mode",
            (
                "Analysts see accepted cases, transaction context, scores, severity "
                "and queue position."
            ),
            (
                "Ground truth must remain hidden because the real outcome is unknown "
                "during live investigation."
            ),
            "🧑‍💻",
        )

    with use2:
        learning_card(
            "Evaluation mode",
            (
                "Researchers can additionally display isFraud and evaluation outcomes."
            ),
            (
                "This supports precision, recall and error analysis."
            ),
            "🧪",
        )

    with use3:
        learning_card(
            "Filtering",
            (
                "The queue should support filters for policy, time step, transaction "
                "type, severity, minimum fraud score and sequential decision."
            ),
            (
                "Filters make large alert queues understandable and auditable."
            ),
            "🔎",
        )

    research_takeaway(
        "Analyst Queue takeaway",
        (
            "The queue is the point where model predictions become human actions. "
            "It should therefore explain not only which alerts were selected, but also "
            "why each alert was prioritised, suppressed or rejected."
        ),
    )

# =========================================================
# PART 3 OF 3
# MONITORING, RESEARCH INTERPRETATION,
# TECHNICAL DETAILS
# =========================================================

# =========================================================
# 6. MONITORING
# =========================================================

with monitoring_tab:
    st.header("Monitoring Performance Over Time")

    section_intro(
        "Why monitor a fraud decision system over time?",
        (
            "Fraud behaviour, analyst workload and alert volume are dynamic. "
            "Monitoring windows reveal whether performance remains stable "
            "throughout the simulation instead of relying on a single summary value."
        ),
    )

    explain1, explain2, explain3 = st.columns(3)

    with explain1:
        learning_card(
            "Monitoring window",
            "A fixed chronological group of transactions.",
            "Allows trends to be analysed rather than only final totals.",
            "🪟",
        )

    with explain2:
        learning_card(
            "Operational drift",
            "Performance may change across time.",
            "A stable system should behave consistently across windows.",
            "📈",
        )

    with explain3:
        learning_card(
            "Early warning",
            "Monitoring identifies periods of overload.",
            "Organisations can react before performance deteriorates.",
            "🚨",
        )

    tabs = st.tabs(["Static Sequential", "Adaptive Sequential"])

    for tab, df, title in [
        (tabs[0], static_windows_df, "Static Sequential"),
        (tabs[1], adaptive_windows_df, "Adaptive Sequential"),
    ]:
        with tab:
            if df.empty:
                st.info("No monitoring data available.")
                continue

            st.markdown(f"### {title}")

            st.dataframe(df, use_container_width=True, hide_index=True)

            chart_candidates = [
                ("alerts", "Accepted alerts"),
                ("candidate_alerts", "Candidate alerts"),
                ("frauds_detected", "Frauds detected"),
                ("frauds_missed", "Frauds missed"),
                ("operational_cost", "Operational cost"),
            ]

            for col, label in chart_candidates:
                if {"window_number", col}.issubset(df.columns):
                    st.markdown(f"#### {label}")
                    st.line_chart(
                        df.set_index("window_number")[[col]],
                        use_container_width=True,
                    )
                    st.caption(
                        f"The chart illustrates how {label.lower()} evolves "
                        "through successive monitoring windows."
                    )

    research_takeaway(
        "Monitoring takeaway",
        (
            "Monitoring transforms the simulation from a one-off evaluation into "
            "a continuously observable operational system."
        ),
    )


# =========================================================
# 7. RESEARCH INTERPRETATION
# =========================================================

with interpretation_tab:
    st.header("Research Interpretation")

    section_intro(
        "What research question is being answered?",
        (
            "Can an adaptive and cost-aware alerting layer improve the operational "
            "usefulness of a fraud detection model compared with a static-threshold baseline?"
        ),
    )

    findings = [
        (
            "Finding 1 – Policy quality",
            "Batch evaluation isolates the decision policy. "
            "Adaptive Batch demonstrates whether the policy itself improves recall "
            "and operational cost before analyst constraints are introduced.",
        ),
        (
            "Finding 2 – Operational reality",
            "Sequential evaluation introduces suppression and analyst capacity. "
            "It measures how much of the theoretical policy improvement can actually "
            "be realised in practice.",
        ),
        (
            "Finding 3 – Capacity is critical",
            "Analyst capacity is an integral component of fraud decision systems. "
            "Even a superior policy cannot improve investigations if accepted alerts "
            "are limited by operational resources.",
        ),
        (
            "Finding 4 – Decision layers matter",
            "The research evaluates more than predictive performance. It demonstrates "
            "how operational decision logic influences business outcomes.",
        ),
        (
            "Finding 5 – Educational contribution",
            "Separating Batch and Sequential evaluation explains why identical machine-"
            "learning models may produce different organisational results.",
        ),
    ]

    for title, body in findings:
        st.markdown(
            f"""
            <div class="decision-card">
                <h3>{title}</h3>
                <p>{body}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Practical implications")

    practical = pd.DataFrame(
        [
            ["Machine Learning", "Produces fraud scores"],
            ["Decision Layer", "Selects operational alerts"],
            ["Sequential Engine", "Applies analyst capacity"],
            ["Monitoring", "Measures long-term stability"],
            ["Analyst Queue", "Prioritises human investigations"],
        ],
        columns=["Component", "Primary role"],
    )

    st.dataframe(practical, use_container_width=True, hide_index=True)

    research_takeaway(
        "Final dissertation conclusion",
        (
            "The research demonstrates that fraud detection performance depends not "
            "only on predictive models but also on operational decision policies, "
            "analyst capacity and continuous monitoring. These components should be "
            "evaluated together as a complete fraud decision system."
        ),
    )


# =========================================================
# 8. TECHNICAL DETAILS
# =========================================================

with technical_tab:
    st.header("Technical Details")

    section_intro(
        "Why include technical details?",
        (
            "Scientific software should be transparent and reproducible. "
            "This section records the parameters that generated the current results."
        ),
    )

    st.markdown("### Current API parameters")
    st.json(simulation_params)

    st.markdown("### Backend parameters")
    st.json(parameters)

    st.markdown("### Raw API response")
    with st.expander("Show raw JSON response"):
        st.json(simulation_data)

    st.markdown("### Reproducibility checklist")

    checklist = pd.DataFrame(
        [
            ["Dataset", "Fixed transaction subset"],
            ["Fraud model", "Pre-scored transactions"],
            ["Decision policy", "Static or Adaptive"],
            ["Sequential settings", "Capacity and suppression"],
            ["Evaluation", "Precision, Recall and Cost"],
            ["Monitoring", "Window-based operational analysis"],
        ],
        columns=["Item", "Current configuration"],
    )

    st.dataframe(
        checklist,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="footer-note">
        Fraud Decision Simulation Dashboard<br>
        MSc Artificial Intelligence Dissertation<br><br>

        This dashboard is designed as an educational companion to the dissertation.
        It explains not only <em>what</em> the fraud decision system achieved,
        but also <em>why</em> each operational outcome occurred.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# END OF DASHBOARD
# =========================================================