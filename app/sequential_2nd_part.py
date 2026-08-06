from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8002"
SIMULATION_ENDPOINT = "simulation/sequential"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPACITY_SWEEP_DIR = PROJECT_ROOT / "metrics" / "capacity_sweep"
CAPACITY_SWEEP_CSV = CAPACITY_SWEEP_DIR / "capacity_sweep_results.csv"
CAPACITY_RECALL_IMAGE = CAPACITY_SWEEP_DIR / "capacity_vs_recall.png"
CAPACITY_DIFFERENCE_IMAGE = CAPACITY_SWEEP_DIR / "capacity_vs_recall_difference.png"
CAPACITY_COST_IMAGE = CAPACITY_SWEEP_DIR / "capacity_vs_operational_cost.png"

st.set_page_config(
    page_title="Sequential Fraud Operations Simulation",
    page_icon="⏱️",
    layout="wide",
)


# =========================================================
# VISUAL STYLE
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    .hero {
        padding: 1.35rem 1.5rem;
        border: 1px solid rgba(30,136,229,.32);
        border-radius: 16px;
        background:
            linear-gradient(
                135deg,
                rgba(25,118,210,.17),
                rgba(239,108,0,.09)
            );
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0 0 .4rem 0;
    }

    .hero p {
        margin: 0;
        opacity: .86;
        line-height: 1.55;
    }

    .section-intro {
        padding: 1rem 1.1rem;
        margin: .45rem 0 1rem;
        border-left: 4px solid #1976d2;
        border-radius: 10px;
        background: rgba(25,118,210,.09);
        line-height: 1.55;
    }

    .metric-card {
        min-height: 158px;
        padding: 1rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
        background: rgba(128,128,128,.045);
    }

    .metric-card .value {
        font-size: 1.72rem;
        font-weight: 700;
        margin: .48rem 0 .35rem;
    }

    .metric-card .note {
        font-size: .9rem;
        opacity: .78;
        line-height: 1.4;
    }

    .tone-blue { border-top: 4px solid #1976d2; }
    .tone-orange { border-top: 4px solid #ef6c00; }
    .tone-green { border-top: 4px solid #2e7d32; }
    .tone-red { border-top: 4px solid #c62828; }

    .takeaway {
        padding: 1rem 1.1rem;
        border-left: 5px solid #2e7d32;
        border-radius: 12px;
        background: rgba(46,125,50,.10);
        line-height: 1.55;
    }

    .warning {
        padding: 1rem 1.1rem;
        border-left: 5px solid #ef6c00;
        border-radius: 12px;
        background: rgba(239,108,0,.10);
        line-height: 1.55;
    }

    .danger {
        padding: 1rem 1.1rem;
        border-left: 5px solid #c62828;
        border-radius: 12px;
        background: rgba(198,40,40,.10);
        line-height: 1.55;
    }

    .parameter-card {
        min-height: 195px;
        padding: 1rem 1.05rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
        background: rgba(128,128,128,.045);
    }

    .parameter-card h3 {
        margin-top: 0;
        font-size: 1.03rem;
    }

    .workflow {
        padding: .9rem 1rem;
        margin: .35rem 0;
        text-align: center;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        background: rgba(128,128,128,.04);
    }

    .arrow {
        text-align: center;
        font-size: 1.35rem;
        opacity: .75;
    }

    .small-note {
        opacity: .72;
        font-size: .86rem;
        line-height: 1.45;
    }

    div[data-testid="stSidebar"] .stExpander {
        border: 1px solid rgba(128,128,128,.28);
        border-radius: 12px;
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


def section_intro(title: str, text: str) -> None:
    st.markdown(
        (
            '<div class="section-intro">'
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
    tone: str = "orange",
) -> None:
    st.markdown(
        f"""
        <div class="metric-card tone-{html.escape(tone)}">
            <strong>{html.escape(title)}</strong>
            <div class="value">{html.escape(value)}</div>
            <div class="note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parameter_card(
    title: str,
    current_value: str,
    meaning: str,
    research_use: str,
    icon: str,
) -> None:
    st.markdown(
        f"""
        <div class="parameter-card">
            <h3>{icon} {html.escape(title)}</h3>
            <p><strong>Current value:</strong> {html.escape(current_value)}</p>
            <p>{html.escape(meaning)}</p>
            <p><strong>Research use:</strong> {html.escape(research_use)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow(title: str, text: str) -> None:
    st.markdown(
        (
            '<div class="workflow">'
            f"<strong>{html.escape(title)}</strong><br>"
            f"{html.escape(text)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def arrow() -> None:
    st.markdown(
        '<div class="arrow">↓</div>',
        unsafe_allow_html=True,
    )


def summary(payload: dict[str, Any], key: str) -> dict[str, Any]:
    return payload.get(key, {}).get("summary", {})


def first_present(
    mapping: dict[str, Any],
    *keys: str,
    default: Any = 0,
) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def normalise_windows(frame: pd.DataFrame) -> pd.DataFrame:
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


def operating_interpretation(
    static_summary: dict[str, Any],
    adaptive_summary: dict[str, Any],
) -> tuple[str, str]:
    recall_diff = (
        n(adaptive_summary.get("recall"))
        - n(static_summary.get("recall"))
    )
    cost_diff = (
        n(adaptive_summary.get("total_operational_cost"))
        - n(static_summary.get("total_operational_cost"))
    )

    if recall_diff > 0 and cost_diff < 0:
        return (
            "takeaway",
            (
                "Adaptive dominates under the current configuration: it detects "
                "a larger share of fraud while producing a lower total operational cost."
            ),
        )

    if recall_diff < 0 and cost_diff > 0:
        return (
            "danger",
            (
                "Static dominates under the current configuration: Adaptive produces "
                "lower recall and higher total operational cost."
            ),
        )

    if abs(recall_diff) < 1e-12 and cost_diff < 0:
        return (
            "takeaway",
            (
                "Both policies achieve the same recall, but Adaptive produces a lower "
                "total operational cost."
            ),
        )

    if abs(recall_diff) < 1e-12 and cost_diff > 0:
        return (
            "warning",
            (
                "Both policies achieve the same recall, but Static produces a lower "
                "total operational cost."
            ),
        )

    if recall_diff > 0:
        return (
            "warning",
            (
                "Adaptive achieves higher recall, but the cost result does not improve "
                "at the same time. This is a performance trade-off rather than dominance."
            ),
        )

    if recall_diff < 0:
        return (
            "warning",
            (
                "Static achieves higher recall, while the cost comparison should be "
                "examined separately."
            ),
        )

    return (
        "warning",
        "The two policies produce equivalent recall and cost under this configuration.",
    )



@st.cache_data(show_spinner=False)
def load_saved_capacity_sweep() -> pd.DataFrame:
    """Load the saved, reproducible capacity experiment."""
    if not CAPACITY_SWEEP_CSV.exists():
        return pd.DataFrame()

    frame = pd.read_csv(CAPACITY_SWEEP_CSV)

    expected_columns = {
        "capacity_per_step",
        "static_recall",
        "adaptive_recall",
        "recall_difference",
        "static_operational_cost",
        "adaptive_operational_cost",
        "winner",
    }

    if not expected_columns.issubset(frame.columns):
        return pd.DataFrame()

    return frame.sort_values("capacity_per_step").reset_index(drop=True)


def saved_capacity_summary(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {}

    best_row = frame.loc[frame["recall_difference"].idxmax()]
    worst_row = frame.loc[frame["recall_difference"].idxmin()]

    return {
        "tested_values": len(frame),
        "adaptive_recall_wins": int((frame["recall_difference"] > 0).sum()),
        "static_recall_wins": int((frame["recall_difference"] < 0).sum()),
        "recall_ties": int((frame["recall_difference"] == 0).sum()),
        "adaptive_lower_cost": int(
            (
                frame["adaptive_operational_cost"]
                < frame["static_operational_cost"]
            ).sum()
        ),
        "static_lower_cost": int(
            (
                frame["adaptive_operational_cost"]
                > frame["static_operational_cost"]
            ).sum()
        ),
        "cost_ties": int(
            (
                frame["adaptive_operational_cost"]
                == frame["static_operational_cost"]
            ).sum()
        ),
        "best_capacity": int(best_row["capacity_per_step"]),
        "best_recall_difference": float(best_row["recall_difference"]),
        "worst_capacity": int(worst_row["capacity_per_step"]),
        "worst_recall_difference": float(worst_row["recall_difference"]),
    }


@st.cache_data(ttl=60, show_spinner=False)
def load_data(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{API_BASE_URL}/{SIMULATION_ENDPOINT}",
        params=params,
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def run_sweep(
    base_params: dict[str, Any],
    parameter_name: str,
    values: Iterable[int | float],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    values_list = list(values)
    progress = st.progress(0)
    status = st.empty()

    for index, value in enumerate(values_list, start=1):
        status.caption(
            f"Running {parameter_name} = {value} "
            f"({index}/{len(values_list)})"
        )

        sweep_params = {
            **base_params,
            parameter_name: value,
        }
        result = load_data(sweep_params)
        static_result = summary(result, "static_sequential")
        adaptive_result = summary(result, "adaptive_sequential")

        static_recall = n(static_result.get("recall"))
        adaptive_recall = n(adaptive_result.get("recall"))
        static_cost = n(static_result.get("total_operational_cost"))
        adaptive_cost = n(adaptive_result.get("total_operational_cost"))

        recall_difference = adaptive_recall - static_recall
        cost_saving = static_cost - adaptive_cost

        if recall_difference > 0 and cost_saving > 0:
            winner = "Adaptive dominates"
        elif recall_difference < 0 and cost_saving < 0:
            winner = "Static dominates"
        elif abs(recall_difference) < 1e-12 and abs(cost_saving) < 1e-12:
            winner = "Tie"
        elif recall_difference > 0:
            winner = "Adaptive higher recall"
        elif recall_difference < 0:
            winner = "Static higher recall"
        elif cost_saving > 0:
            winner = "Adaptive lower cost"
        else:
            winner = "Static lower cost"

        rows.append(
            {
                parameter_name: value,
                "Static recall": static_recall,
                "Adaptive recall": adaptive_recall,
                "Recall difference": recall_difference,
                "Static cost": static_cost,
                "Adaptive cost": adaptive_cost,
                "Adaptive cost saving": cost_saving,
                "Static accepted": i(
                    first_present(
                        static_result,
                        "selected_alerts",
                        "alerts",
                    )
                ),
                "Adaptive accepted": i(
                    first_present(
                        adaptive_result,
                        "selected_alerts",
                        "alerts",
                    )
                ),
                "Static suppressed": i(
                    first_present(
                        static_result,
                        "suppressed_alerts",
                        "suppressed",
                    )
                ),
                "Adaptive suppressed": i(
                    first_present(
                        adaptive_result,
                        "suppressed_alerts",
                        "suppressed",
                    )
                ),
                "Adaptive candidates": i(
                    first_present(
                        adaptive_result,
                        "policy_candidate_alerts",
                        "candidate_alerts",
                    )
                ),
                "Winner": winner,
            }
        )

        progress.progress(index / len(values_list))

    status.empty()
    progress.empty()

    return pd.DataFrame(rows)


def display_sweep(
    frame: pd.DataFrame,
    parameter_name: str,
    parameter_label: str,
) -> None:
    if frame.empty:
        st.info("No sensitivity results are available yet.")
        return

    display = frame.copy()
    for column in [
        "Static recall",
        "Adaptive recall",
        "Recall difference",
    ]:
        display[column] = display[column].map(
            lambda value: f"{n(value):+.2%}"
            if column == "Recall difference"
            else f"{n(value):.2%}"
        )

    for column in [
        "Static cost",
        "Adaptive cost",
        "Adaptive cost saving",
    ]:
        display[column] = display[column].map(money)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Recall comparison")
    recall_chart = frame[
        [
            parameter_name,
            "Static recall",
            "Adaptive recall",
        ]
    ].set_index(parameter_name)
    st.line_chart(recall_chart, use_container_width=True)

    st.markdown("#### Adaptive recall advantage")
    difference_chart = frame[
        [
            parameter_name,
            "Recall difference",
        ]
    ].set_index(parameter_name)
    st.line_chart(difference_chart, use_container_width=True)

    st.markdown("#### Operational-cost comparison")
    cost_chart = frame[
        [
            parameter_name,
            "Static cost",
            "Adaptive cost",
        ]
    ].set_index(parameter_name)
    st.line_chart(cost_chart, use_container_width=True)

    adaptive_wins = int(
        frame["Winner"].astype(str).str.startswith("Adaptive").sum()
    )
    static_wins = int(
        frame["Winner"].astype(str).str.startswith("Static").sum()
    )
    ties = int((frame["Winner"] == "Tie").sum())

    best_row = frame.loc[frame["Recall difference"].idxmax()]
    worst_row = frame.loc[frame["Recall difference"].idxmin()]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            "Adaptive wins",
            str(adaptive_wins),
            f"out of {len(frame)} tested values",
            "green",
        )
    with c2:
        metric_card(
            "Static wins",
            str(static_wins),
            f"out of {len(frame)} tested values",
            "red",
        )
    with c3:
        metric_card(
            "Ties",
            str(ties),
            f"out of {len(frame)} tested values",
            "blue",
        )
    with c4:
        metric_card(
            "Best Adaptive point",
            str(best_row[parameter_name]),
            (
                f"{best_row['Recall difference']:+.2%} recall difference"
            ),
            "orange",
        )

    st.markdown(
        f"""
        <div class="takeaway">
            <strong>Sensitivity interpretation</strong><br>
            Across the tested {html.escape(parameter_label.lower())} values,
            Adaptive achieved its largest recall advantage at
            <strong>{html.escape(str(best_row[parameter_name]))}</strong>
            ({best_row['Recall difference']:+.2%}).
            Its weakest relative result occurred at
            <strong>{html.escape(str(worst_row[parameter_name]))}</strong>
            ({worst_row['Recall difference']:+.2%}).
        </div>
        """,
        unsafe_allow_html=True,
    )

    csv = frame.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download {parameter_label.lower()} sensitivity results",
        data=csv,
        file_name=f"{parameter_name}_sensitivity.csv",
        mime="text/csv",
        use_container_width=True,
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>⏱️ Sequential Fraud Operations Simulation</h1>
        <p>
            Operational evaluation of Static and Adaptive fraud-alert policies under
            chronological replay, limited analyst capacity, repeat-alert suppression
            and configurable Adaptive workload.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("Sequential experiment")

st.sidebar.caption(
    "The three highlighted controls are the main sensitivity variables. "
    "Change one at a time when interpreting results."
)

with st.sidebar.expander(
    "🎛️ Main sensitivity controls",
    expanded=True,
):
    alert_budget_per_step = st.number_input(
        "1. Analyst capacity — alerts per step",
        min_value=1,
        max_value=5000,
        value=30,
        step=5,
        help=(
            "Maximum number of alerts that analysts can accept during each "
            "chronological simulation step."
        ),
    )

    suppression_window = st.number_input(
        "2. Suppression window — steps",
        min_value=0,
        max_value=100,
        value=3,
        step=1,
        help=(
            "Number of subsequent steps during which repeated alerts for the "
            "same entity may be suppressed."
        ),
    )

    budget_multiplier = st.slider(
        "3. Adaptive budget multiplier",
        min_value=0.5,
        max_value=2.5,
        value=1.4,
        step=0.1,
        help=(
            "Controls how large the Adaptive candidate-alert budget can become "
            "relative to the Static baseline."
        ),
    )

with st.sidebar.expander(
    "🔒 Fixed policy and cost assumptions",
    expanded=False,
):
    transaction_limit = st.selectbox(
        "Transactions evaluated",
        [1000, 3000, 10000, 50000],
        index=2,
    )

    investigation_cost = st.number_input(
        "Cost per investigation",
        min_value=0.0,
        value=10.0,
        step=1.0,
    )

    static_threshold = st.slider(
        "Static fraud threshold",
        0.0,
        1.0,
        0.5,
        0.01,
    )

    risk_zone_floor = st.slider(
        "Risk-zone floor",
        0.0,
        1.0,
        0.30,
        0.01,
    )

    monitoring_window_size = st.selectbox(
        "Transactions per monitoring window",
        [250, 500, 1000, 2500, 5000],
        index=2,
    )

if st.sidebar.button(
    "Refresh current result",
    use_container_width=True,
):
    st.cache_data.clear()

st.sidebar.divider()
st.sidebar.markdown(
    """
    **Recommended experimental procedure**

    1. Keep fixed assumptions unchanged.  
    2. Change only one sensitivity control.  
    3. Compare Static and Adaptive recall and cost.  
    4. Confirm findings with the automated sensitivity tabs.
    """
)
st.sidebar.caption(f"API: `{API_BASE_URL}`")


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
    "monitoring_window_size": int(monitoring_window_size),
}


# =========================================================
# CURRENT API REQUEST
# =========================================================

try:
    with st.spinner("Running the current chronological simulation..."):
        data = load_data(params)
except requests.exceptions.ConnectionError:
    st.error(
        "FastAPI is not available. Run:\n\n"
        "`py -m uvicorn app.api.main:app --reload --port 8002`"
    )
    st.stop()
except requests.exceptions.Timeout:
    st.error(
        "The API request timed out. Try a smaller transaction limit."
    )
    st.stop()
except requests.exceptions.HTTPError as exc:
    st.error("FastAPI returned an error.")
    if exc.response is not None:
        try:
            st.json(exc.response.json())
        except ValueError:
            st.code(exc.response.text)
    st.stop()
except requests.exceptions.RequestException as exc:
    st.error("The API request failed.")
    st.exception(exc)
    st.stop()


static = summary(data, "static_sequential")
adaptive = summary(data, "adaptive_sequential")
parameters = data.get("parameters", {})

static_windows = normalise_windows(
    pd.DataFrame(
        data.get("static_sequential", {}).get("monitoring_windows", [])
    )
)
adaptive_windows = normalise_windows(
    pd.DataFrame(
        data.get("adaptive_sequential", {}).get("monitoring_windows", [])
    )
)

saved_capacity_frame = load_saved_capacity_sweep()
saved_capacity_stats = saved_capacity_summary(saved_capacity_frame)


# =========================================================
# NAVIGATION
# =========================================================

(
    summary_tab,
    sensitivity_tab,
    capacity_tab,
    suppression_tab,
    aggressiveness_tab,
    workflow_tab,
    queue_tab,
    monitoring_tab,
    interpretation_tab,
    technical_tab,
) = st.tabs(
    [
        "1. Executive Summary",
        "2. Sensitivity Overview",
        "3. Analyst Capacity",
        "4. Suppression Impact",
        "5. Adaptive Aggressiveness",
        "6. Sequential Workflow",
        "7. Analyst Queue",
        "8. Monitoring",
        "9. Research Interpretation",
        "10. Technical Details",
    ]
)


# =========================================================
# 1. EXECUTIVE SUMMARY
# =========================================================

with summary_tab:
    st.header("Executive Summary")

    section_intro(
        "What does this dashboard answer?",
        (
            "How do analyst capacity, repeat-alert suppression and Adaptive "
            "candidate-generation intensity affect whether the Adaptive policy "
            "outperforms the Static baseline under sequential operating conditions?"
        ),
    )

    recall_difference = (
        n(adaptive.get("recall"))
        - n(static.get("recall"))
    )
    cost_difference = (
        n(adaptive.get("total_operational_cost"))
        - n(static.get("total_operational_cost"))
    )

    cols = st.columns(4)

    with cols[0]:
        metric_card(
            "Adaptive recall",
            pct(adaptive.get("recall")),
            f"{recall_difference:+.2%} versus Static Sequential",
            "blue" if recall_difference == 0 else (
                "green" if recall_difference > 0 else "red"
            ),
        )

    with cols[1]:
        metric_card(
            "Adaptive accepted alerts",
            f"{i(adaptive.get('selected_alerts')):,}",
            (
                f"from {i(adaptive.get('policy_candidate_alerts')):,} "
                "candidate alerts"
            ),
            "orange",
        )

    with cols[2]:
        metric_card(
            "Adaptive capacity rejected",
            f"{i(adaptive.get('capacity_rejected_alerts')):,}",
            "valid candidates that could not enter the analyst queue",
            "red",
        )

    with cols[3]:
        metric_card(
            "Adaptive operational cost",
            money(adaptive.get("total_operational_cost")),
            f"{money(cost_difference)} versus Static",
            "green" if cost_difference < 0 else "orange",
        )

    interpretation_class, interpretation_text = operating_interpretation(
        static,
        adaptive,
    )

    st.markdown(
        f"""
        <div class="{interpretation_class}">
            <strong>Current operating conclusion</strong><br>
            {html.escape(interpretation_text)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### The three variables that shape the Sequential result")

    p1, p2, p3 = st.columns(3)

    with p1:
        parameter_card(
            "Analyst capacity",
            f"{int(alert_budget_per_step)} alerts per step",
            (
                "Defines how many candidate alerts can become real analyst "
                "investigations during each chronological period."
            ),
            (
                "Tests whether additional Adaptive candidates can actually reach "
                "human review."
            ),
            "👥",
        )

    with p2:
        parameter_card(
            "Repeat-alert suppression",
            f"{int(suppression_window)} steps",
            (
                "Controls how long repeated entity alerts may be removed from "
                "the queue to reduce duplicate workload."
            ),
            (
                "Tests the trade-off between alert-fatigue reduction and the risk "
                "of suppressing useful repeated warnings."
            ),
            "🔁",
        )

    with p3:
        parameter_card(
            "Adaptive aggressiveness",
            f"{budget_multiplier:.1f}× budget multiplier",
            (
                "Controls how broadly the Adaptive policy expands the candidate "
                "alert set beyond the Static baseline."
            ),
            (
                "Tests whether broader fraud coverage creates operational value "
                "or merely increases queue pressure."
            ),
            "🧠",
        )


# =========================================================
# 2. SENSITIVITY OVERVIEW
# =========================================================

with sensitivity_tab:
    st.header("Operational Sensitivity Overview")

    section_intro(
        "Why test these three parameters?",
        (
            "They represent three distinct operational decisions: available human "
            "resources, duplicate-alert management and the intensity of Adaptive "
            "candidate generation. Testing them separately prevents their effects "
            "from being confused."
        ),
    )

    overview = pd.DataFrame(
        [
            {
                "Sensitivity variable": "Analyst capacity",
                "API parameter": "alert_budget_per_step",
                "Main operational question":
                    "How many alerts can analysts review per time step?",
                "Primary outcomes":
                    "Recall, accepted alerts, capacity rejection and cost",
            },
            {
                "Sensitivity variable": "Suppression policy",
                "API parameter": "suppression_window",
                "Main operational question":
                    "How strongly should repeated entity alerts be filtered?",
                "Primary outcomes":
                    "Suppressed alerts, recall, workload and cost",
            },
            {
                "Sensitivity variable": "Adaptive aggressiveness",
                "API parameter": "budget_multiplier",
                "Main operational question":
                    "How broadly should Adaptive expand the candidate set?",
                "Primary outcomes":
                    "Candidates, recall, precision, overflow and cost",
            },
        ]
    )

    st.dataframe(
        overview,
        use_container_width=True,
        hide_index=True,
    )

    current = pd.DataFrame(
        [
            {
                "Setting": "Analyst capacity",
                "Current value": int(alert_budget_per_step),
            },
            {
                "Setting": "Suppression window",
                "Current value": int(suppression_window),
            },
            {
                "Setting": "Adaptive budget multiplier",
                "Current value": float(budget_multiplier),
            },
        ]
    )

    st.markdown("### Current sensitivity configuration")
    st.dataframe(current, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="warning">
            <strong>Experimental rule</strong><br>
            Change one sensitivity variable at a time while all other parameters
            remain fixed. Otherwise, the cause of an observed performance change
            cannot be isolated.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 3. ANALYST CAPACITY
# =========================================================

with capacity_tab:
    st.header("Analyst Capacity Sensitivity")

    section_intro(
        "What does analyst capacity test?",
        (
            "It tests how much of the Adaptive policy's broader candidate selection "
            "can be converted into real investigations when each chronological step "
            "has a limited number of analyst slots."
        ),
    )

    st.markdown("## General capacity-study result")

    if saved_capacity_frame.empty:
        st.warning(
            "No saved capacity-sweep result was found. Run "
            "`py scripts\\run_capacity_sweep.py` once from the project root. "
            "The dashboard will then load the CSV and figures automatically."
        )
    else:
        section_intro(
            "What does the completed experiment show?",
            (
                "The saved study compares Static and Adaptive Sequential performance "
                "across multiple analyst-capacity levels while every other parameter "
                "remains fixed. This is the general capacity result and does not depend "
                "on the current sidebar value."
            ),
        )

        g1, g2, g3, g4 = st.columns(4)

        with g1:
            metric_card(
                "Adaptive recall wins",
                str(saved_capacity_stats["adaptive_recall_wins"]),
                (
                    f"out of {saved_capacity_stats['tested_values']} "
                    "tested capacity levels"
                ),
                "green",
            )

        with g2:
            metric_card(
                "Static recall wins",
                str(saved_capacity_stats["static_recall_wins"]),
                (
                    f"with {saved_capacity_stats['recall_ties']} "
                    "recall ties"
                ),
                "red",
            )

        with g3:
            metric_card(
                "Adaptive lower-cost cases",
                str(saved_capacity_stats["adaptive_lower_cost"]),
                (
                    f"out of {saved_capacity_stats['tested_values']} "
                    "tested capacity levels"
                ),
                "green",
            )

        with g4:
            metric_card(
                "Largest Adaptive advantage",
                f"{saved_capacity_stats['best_recall_difference']:+.2%}",
                (
                    "observed at capacity "
                    f"{saved_capacity_stats['best_capacity']}"
                ),
                "orange",
            )

        st.markdown(
            f"""
            <div class="takeaway">
                <strong>Overall capacity finding</strong><br>
                Adaptive achieved higher recall in
                <strong>{saved_capacity_stats['adaptive_recall_wins']}</strong>
                of the {saved_capacity_stats['tested_values']} tested capacity levels.
                Static achieved higher recall in
                <strong>{saved_capacity_stats['static_recall_wins']}</strong>,
                while <strong>{saved_capacity_stats['recall_ties']}</strong>
                settings were recall ties. Adaptive produced lower operational cost in
                <strong>{saved_capacity_stats['adaptive_lower_cost']}</strong>
                settings. Its largest recall advantage was
                <strong>{saved_capacity_stats['best_recall_difference']:+.2%}</strong>
                at capacity
                <strong>{saved_capacity_stats['best_capacity']}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Complete saved capacity results")

        saved_display = saved_capacity_frame.copy()

        for column in [
            "static_recall",
            "adaptive_recall",
            "recall_difference",
        ]:
            saved_display[column] = saved_display[column].map(
                lambda value, current_column=column: (
                    f"{value:+.2%}"
                    if current_column == "recall_difference"
                    else f"{value:.2%}"
                )
            )

        for column in [
            "static_operational_cost",
            "adaptive_operational_cost",
        ]:
            saved_display[column] = saved_display[column].map(money)

        saved_display = saved_display.rename(
            columns={
                "capacity_per_step": "Capacity per step",
                "static_recall": "Static recall",
                "adaptive_recall": "Adaptive recall",
                "recall_difference": "Recall difference",
                "static_operational_cost": "Static cost",
                "adaptive_operational_cost": "Adaptive cost",
                "winner": "Winner",
            }
        )

        preferred_columns = [
            "Capacity per step",
            "Static recall",
            "Adaptive recall",
            "Recall difference",
            "Static cost",
            "Adaptive cost",
            "Winner",
        ]

        st.dataframe(
            saved_display[
                [
                    column
                    for column in preferred_columns
                    if column in saved_display.columns
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Capacity-study figures")

        if CAPACITY_RECALL_IMAGE.exists():
            st.image(
                str(CAPACITY_RECALL_IMAGE),
                caption=(
                    "Static and Adaptive Sequential recall across analyst capacity."
                ),
                use_container_width=True,
            )

        if CAPACITY_DIFFERENCE_IMAGE.exists():
            st.image(
                str(CAPACITY_DIFFERENCE_IMAGE),
                caption=(
                    "Adaptive recall advantage relative to Static. "
                    "Values above zero favour Adaptive."
                ),
                use_container_width=True,
            )

        if CAPACITY_COST_IMAGE.exists():
            st.image(
                str(CAPACITY_COST_IMAGE),
                caption=(
                    "Total operational cost across capacity levels. "
                    "Lower values are preferable."
                ),
                use_container_width=True,
            )

        st.markdown(
            f"""
            <div class="warning">
                <strong>General interpretation</strong><br>
                The capacity study does not show universal superiority at every
                single point. It shows a capacity-dependent pattern: Adaptive is
                stronger across most tested settings and becomes especially effective
                once enough analyst capacity is available, while isolated capacities
                can still produce ties or a Static advantage. The weakest Adaptive
                point occurred at capacity
                <strong>{saved_capacity_stats['worst_capacity']}</strong>
                ({saved_capacity_stats['worst_recall_difference']:+.2%} recall difference).
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("## Current sidebar configuration")

    unique_steps = i(parameters.get("unique_steps"))
    max_capacity = i(parameters.get("maximum_sequential_capacity"))

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Current capacity per step",
            f"{int(alert_budget_per_step):,}",
            "maximum accepted investigations per chronological step",
            "orange",
        )

    with c2:
        metric_card(
            "Chronological steps",
            f"{unique_steps:,}",
            "periods to which separate capacity limits are applied",
            "blue",
        )

    with c3:
        metric_card(
            "Maximum theoretical capacity",
            f"{max_capacity:,}",
            "capacity per step multiplied by the number of steps",
            "blue",
        )

    with c4:
        metric_card(
            "Adaptive overflow",
            f"{i(adaptive.get('capacity_rejected_alerts')):,}",
            "candidate alerts rejected because capacity was exhausted",
            "red",
        )

    rows = []
    for label, result in [
        ("Static Sequential", static),
        ("Adaptive Sequential", adaptive),
    ]:
        candidates = i(result.get("policy_candidate_alerts"))
        accepted = i(result.get("selected_alerts"))
        rows.append(
            {
                "Scenario": label,
                "Candidate alerts": candidates,
                "Accepted alerts": accepted,
                "Suppressed alerts": i(result.get("suppressed_alerts")),
                "Capacity rejected": i(
                    result.get("capacity_rejected_alerts")
                ),
                "Acceptance rate":
                    accepted / candidates if candidates else 0.0,
                "Recall": n(result.get("recall")),
                "Operational cost": n(
                    result.get("total_operational_cost")
                ),
            }
        )

    capacity_current = pd.DataFrame(rows)
    capacity_display = capacity_current.copy()
    capacity_display["Acceptance rate"] = (
        capacity_display["Acceptance rate"].map(
            lambda value: f"{value:.2%}"
        )
    )
    capacity_display["Recall"] = capacity_display["Recall"].map(
        lambda value: f"{value:.2%}"
    )
    capacity_display["Operational cost"] = (
        capacity_display["Operational cost"].map(money)
    )

    st.markdown("### Current capacity result")
    st.dataframe(
        capacity_display,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        capacity_current.set_index("Scenario")[
            [
                "Accepted alerts",
                "Suppressed alerts",
                "Capacity rejected",
            ]
        ],
        use_container_width=True,
    )

    st.markdown("### Optional: run a new capacity sweep")
    st.caption(
        "The saved general study above remains visible automatically. "
        "Use the controls below only when you intentionally want to run a new experiment."
    )

    capacity_values = st.multiselect(
        "Capacity values to test",
        options=list(range(10, 201, 10)),
        default=[
            10, 20, 30, 40, 50, 60, 70, 80,
            90, 100, 110, 120, 130, 140, 150,
        ],
        key="capacity_values",
    )

    if st.button(
        "Run analyst-capacity sensitivity",
        use_container_width=True,
        key="run_capacity_sensitivity",
    ):
        if not capacity_values:
            st.warning("Select at least one capacity value.")
        else:
            try:
                with st.spinner("Running capacity sensitivity..."):
                    st.session_state["capacity_sweep"] = run_sweep(
                        params,
                        "alert_budget_per_step",
                        sorted(capacity_values),
                    )
            except requests.exceptions.RequestException as exc:
                st.error("Capacity sensitivity failed.")
                st.exception(exc)

    capacity_sweep = st.session_state.get(
        "capacity_sweep",
        pd.DataFrame(),
    )
    display_sweep(
        capacity_sweep,
        "alert_budget_per_step",
        "Analyst capacity",
    )


# =========================================================
# 4. SUPPRESSION IMPACT
# =========================================================

with suppression_tab:
    st.header("Repeat-Alert Suppression Sensitivity")

    section_intro(
        "What does suppression test?",
        (
            "Suppression reduces repeated alerts for the same entity during a "
            "cooldown period. The experiment tests whether duplicate-workload "
            "reduction improves efficiency or removes useful repeated warnings."
        ),
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        metric_card(
            "Current suppression window",
            f"{int(suppression_window)} steps",
            "cooldown length applied to repeated entity alerts",
            "orange",
        )

    with s2:
        metric_card(
            "Static suppressed",
            f"{i(static.get('suppressed_alerts')):,}",
            "Static candidates removed as repeated alerts",
            "blue",
        )

    with s3:
        metric_card(
            "Adaptive suppressed",
            f"{i(adaptive.get('suppressed_alerts')):,}",
            "Adaptive candidates removed as repeated alerts",
            "blue",
        )

    with s4:
        metric_card(
            "Adaptive recall",
            pct(adaptive.get("recall")),
            "fraud coverage after suppression and capacity",
            "green" if recall_difference > 0 else "orange",
        )

    suppression_values = st.multiselect(
        "Suppression-window values to test",
        options=list(range(0, 16)),
        default=[0, 1, 2, 3, 5, 7, 10],
        key="suppression_values",
    )

    if st.button(
        "Run suppression sensitivity",
        use_container_width=True,
        key="run_suppression_sensitivity",
    ):
        if not suppression_values:
            st.warning("Select at least one suppression-window value.")
        else:
            try:
                with st.spinner("Running suppression sensitivity..."):
                    st.session_state["suppression_sweep"] = run_sweep(
                        params,
                        "suppression_window",
                        sorted(suppression_values),
                    )
            except requests.exceptions.RequestException as exc:
                st.error("Suppression sensitivity failed.")
                st.exception(exc)

    suppression_sweep = st.session_state.get(
        "suppression_sweep",
        pd.DataFrame(),
    )
    display_sweep(
        suppression_sweep,
        "suppression_window",
        "Suppression window",
    )


# =========================================================
# 5. ADAPTIVE AGGRESSIVENESS
# =========================================================

with aggressiveness_tab:
    st.header("Adaptive Aggressiveness Sensitivity")

    section_intro(
        "What does the budget multiplier test?",
        (
            "The multiplier determines how far the Adaptive policy may expand its "
            "candidate workload beyond the Static baseline. A larger value may "
            "increase fraud coverage, but it can also increase queue pressure, "
            "capacity rejection and investigation cost."
        ),
    )

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        metric_card(
            "Current multiplier",
            f"{budget_multiplier:.1f}×",
            "Adaptive candidate-budget intensity",
            "orange",
        )

    with a2:
        metric_card(
            "Adaptive candidates",
            f"{i(adaptive.get('policy_candidate_alerts')):,}",
            "transactions proposed for sequential consideration",
            "blue",
        )

    with a3:
        metric_card(
            "Adaptive accepted",
            f"{i(adaptive.get('selected_alerts')):,}",
            "candidate alerts that reached analyst review",
            "green",
        )

    with a4:
        candidate_count = i(adaptive.get("policy_candidate_alerts"))
        rejected_count = i(adaptive.get("capacity_rejected_alerts"))
        rejection_rate = (
            rejected_count / candidate_count
            if candidate_count else 0.0
        )
        metric_card(
            "Adaptive rejection rate",
            pct(rejection_rate),
            "share of candidates left outside analyst capacity",
            "red",
        )

    multiplier_values = st.multiselect(
        "Budget-multiplier values to test",
        options=[
            round(value / 10, 1)
            for value in range(5, 26)
        ],
        default=[0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0],
        key="multiplier_values",
    )

    if st.button(
        "Run Adaptive-aggressiveness sensitivity",
        use_container_width=True,
        key="run_multiplier_sensitivity",
    ):
        if not multiplier_values:
            st.warning("Select at least one budget-multiplier value.")
        else:
            try:
                with st.spinner(
                    "Running Adaptive-aggressiveness sensitivity..."
                ):
                    st.session_state["multiplier_sweep"] = run_sweep(
                        params,
                        "budget_multiplier",
                        sorted(multiplier_values),
                    )
            except requests.exceptions.RequestException as exc:
                st.error("Adaptive-aggressiveness sensitivity failed.")
                st.exception(exc)

    multiplier_sweep = st.session_state.get(
        "multiplier_sweep",
        pd.DataFrame(),
    )
    display_sweep(
        multiplier_sweep,
        "budget_multiplier",
        "Adaptive budget multiplier",
    )


# =========================================================
# 6. WORKFLOW
# =========================================================

with workflow_tab:
    st.header("Sequential Workflow")

    section_intro(
        "Why chronological replay?",
        (
            "A global candidate-alert set does not show when alerts arrive or "
            "whether analysts have enough capacity at each moment. Sequential "
            "replay adds time, suppression and resource constraints."
        ),
    )

    steps = [
        (
            "1. Candidate alerts",
            "Static or Adaptive policy proposes alerts.",
        ),
        (
            "2. Chronological grouping",
            "Alerts are processed in the transaction step in which they occurred.",
        ),
        (
            "3. Suppression",
            "Repeated entity alerts inside the cooldown window may be removed.",
        ),
        (
            "4. Priority ordering",
            "Remaining alerts are ranked within the current time step.",
        ),
        (
            "5. Capacity allocation",
            "Highest-priority alerts are accepted until the step limit is reached.",
        ),
        (
            "6. Outcome evaluation",
            "Accepted alerts are compared with ground truth for recall, precision and cost.",
        ),
    ]

    for index, (title, text) in enumerate(steps):
        workflow(title, text)
        if index < len(steps) - 1:
            arrow()


# =========================================================
# 7. ANALYST QUEUE
# =========================================================

with queue_tab:
    st.header("Analyst Queue")

    section_intro(
        "What reaches the analyst?",
        (
            "Only accepted alerts form the operational queue. Suppressed or "
            "capacity-rejected candidates remain useful for audit and retrospective "
            "evaluation but are not investigated in the current simulation."
        ),
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        metric_card(
            "Adaptive candidates",
            f"{i(adaptive.get('policy_candidate_alerts')):,}",
            "proposed by the Adaptive decision policy",
            "orange",
        )

    with q2:
        metric_card(
            "Accepted",
            f"{i(adaptive.get('selected_alerts')):,}",
            "entered the analyst workload",
            "green",
        )

    with q3:
        metric_card(
            "Suppressed",
            f"{i(adaptive.get('suppressed_alerts')):,}",
            "removed as repeated entity alerts",
            "blue",
        )

    with q4:
        metric_card(
            "Capacity overflow",
            f"{i(adaptive.get('capacity_rejected_alerts')):,}",
            "could not be investigated in the current step",
            "red",
        )

    st.markdown("### Recommended transaction-level queue fields")

    queue_fields = pd.DataFrame(
        [
            ["transaction_id", "Unique transaction identifier"],
            ["step", "Chronological simulation step"],
            ["type", "Transaction category"],
            ["amount", "Transaction value"],
            ["fraud_score", "Model risk estimate"],
            ["rank_score", "Decision priority"],
            ["candidate_priority_rank", "Rank within current step"],
            [
                "sequential_decision",
                "alert / suppressed / capacity_rejected",
            ],
            [
                "selected_alert",
                "Whether the analyst receives the case",
            ],
            [
                "isFraud",
                "Ground truth for retrospective evaluation only",
            ],
        ],
        columns=["Queue field", "Operational meaning"],
    )

    st.dataframe(
        queue_fields,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 8. MONITORING
# =========================================================

with monitoring_tab:
    st.header("Monitoring Performance Over Time")

    section_intro(
        "Why monitor by window?",
        (
            "Summary values can hide overload or deterioration in individual "
            "periods. Monitoring windows reveal temporal variation in workload, "
            "missed fraud and operational cost."
        ),
    )

    monitoring_tabs = st.tabs(
        ["Static Sequential", "Adaptive Sequential"]
    )

    for tab, frame, title in [
        (
            monitoring_tabs[0],
            static_windows,
            "Static Sequential",
        ),
        (
            monitoring_tabs[1],
            adaptive_windows,
            "Adaptive Sequential",
        ),
    ]:
        with tab:
            if frame.empty:
                st.info("No monitoring data are available.")
                continue

            st.markdown(f"### {title}")
            st.dataframe(
                frame,
                use_container_width=True,
                hide_index=True,
            )

            chart_candidates = [
                ("alerts", "Accepted alerts"),
                ("candidate_alerts", "Candidate alerts"),
                ("capacity_rejected", "Capacity rejected"),
                ("suppressed", "Suppressed alerts"),
                ("frauds_detected", "Frauds detected"),
                ("frauds_missed", "Frauds missed"),
                ("operational_cost", "Operational cost"),
            ]

            for column, label in chart_candidates:
                if {
                    "window_number",
                    column,
                }.issubset(frame.columns):
                    st.markdown(f"#### {label}")
                    st.line_chart(
                        frame.set_index("window_number")[[column]],
                        use_container_width=True,
                    )


# =========================================================
# 9. RESEARCH INTERPRETATION
# =========================================================

with interpretation_tab:
    st.header("Research Interpretation")

    section_intro(
        "Research focus",
        (
            "Sequential evaluation addresses operational feasibility: the "
            "interaction between policy quality, chronology, suppression, "
            "Adaptive candidate generation and analyst capacity."
        ),
    )

    gain = (
        n(adaptive.get("recall"))
        - n(static.get("recall"))
    )

    cost_saving = (
        n(static.get("total_operational_cost"))
        - n(adaptive.get("total_operational_cost"))
    )

    st.markdown(
        f"""
        <div class="takeaway">
            <strong>RQ3 — Operational alert management</strong><br>
            The Adaptive policy generated
            <strong>{i(adaptive.get('policy_candidate_alerts')):,}</strong>
            candidates. Of these,
            <strong>{i(adaptive.get('selected_alerts')):,}</strong>
            entered the analyst queue,
            <strong>{i(adaptive.get('capacity_rejected_alerts')):,}</strong>
            were rejected for capacity and
            <strong>{i(adaptive.get('suppressed_alerts')):,}</strong>
            were suppressed.
        </div>
        <br>
        <div class="takeaway">
            <strong>RQ4 — Sequential behaviour</strong><br>
            Under the current configuration, Adaptive changes recall by
            <strong>{gain:+.2%}</strong> and changes operational cost by
            <strong>{money(-cost_saving)}</strong> relative to Static.
        </div>
        <br>
        <div class="warning">
            <strong>Methodological interpretation</strong><br>
            No single setting proves universal superiority. The sensitivity
            experiments identify the operating ranges in which Adaptive,
            Static or neither policy produces the stronger outcome.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Current configuration statement")

    if gain > 0 and cost_saving > 0:
        conclusion = (
            "Adaptive is operationally superior under the selected configuration "
            "because it combines higher fraud recall with lower total cost."
        )
    elif gain == 0 and cost_saving > 0:
        conclusion = (
            "Adaptive provides equal fraud coverage with lower cost under the "
            "selected configuration."
        )
    elif gain > 0:
        conclusion = (
            "Adaptive provides higher fraud coverage, but the improvement involves "
            "a cost trade-off."
        )
    elif gain < 0 and cost_saving < 0:
        conclusion = (
            "Static is operationally superior under the selected configuration."
        )
    else:
        conclusion = (
            "The current configuration produces a mixed or equivalent result. "
            "Sensitivity analysis is required for a defensible conclusion."
        )

    st.markdown(
        f"""
        <div class="section-intro">
            <strong>Defensible conclusion for this run</strong><br>
            {html.escape(conclusion)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 10. TECHNICAL DETAILS
# =========================================================

with technical_tab:
    st.header("Technical Details")

    section_intro(
        "Why include technical details?",
        (
            "The parameter values and raw API response make every displayed "
            "result transparent and reproducible."
        ),
    )

    st.markdown("### Current API parameters")
    st.json(params)

    st.markdown("### Backend parameters")
    st.json(parameters)

    with st.expander("Show raw API response"):
        st.json(data)

    st.markdown(
        """
        <div class="small-note">
            Sensitivity runs use the same FastAPI endpoint and modify only the
            selected parameter. No backend or Uvicorn changes are required.
        </div>
        """,
        unsafe_allow_html=True,
    )