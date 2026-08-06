import html
from typing import Any

import pandas as pd
import requests
import streamlit as st


# =========================================================
# Configuration
# =========================================================

API_BASE_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Adaptive Fraud Intelligence",
    page_icon="🛡️",
    layout="wide",
)


# =========================================================
# Visual styling
# =========================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.3rem 1.5rem;
            border: 1px solid rgba(128, 128, 128, 0.24);
            border-radius: 16px;
            margin-bottom: 1rem;
            background: linear-gradient(
                135deg,
                rgba(30, 136, 229, 0.13),
                rgba(67, 160, 71, 0.07)
            );
        }

        .hero h1 {
            margin: 0 0 0.35rem 0;
            font-size: 2.05rem;
        }

        .hero p {
            margin: 0;
            color: rgba(230, 230, 230, 0.78);
            font-size: 1rem;
        }

        .simple-card {
            min-height: 175px;
            padding: 1rem;
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 14px;
            background: rgba(128, 128, 128, 0.055);
        }

        .simple-card .icon {
            font-size: 1.55rem;
            margin-bottom: 0.4rem;
        }

        .simple-card h3 {
            margin: 0;
            font-size: 1.05rem;
            font-weight: 600;
        }

        .simple-card .value {
            font-size: 1.85rem;
            font-weight: 700;
            margin: 0.35rem 0;
        }

        .simple-card .explanation {
            font-size: 0.9rem;
            line-height: 1.35;
            color: rgba(220, 220, 220, 0.72);
        }

        .positive-card {
            border-top: 4px solid #2e7d32;
        }

        .neutral-card {
            border-top: 4px solid #ef6c00;
        }

        .negative-card {
            border-top: 4px solid #c62828;
        }

        .workflow-step {
            text-align: center;
            padding: 0.85rem 0.55rem;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.28);
            background: rgba(128, 128, 128, 0.06);
            min-height: 118px;
        }

        .workflow-step .number {
            font-size: 1.75rem;
            font-weight: 700;
            margin-top: 0.2rem;
        }

        .workflow-step .label {
            font-size: 0.92rem;
            color: rgba(220, 220, 220, 0.74);
        }

        .arrow {
            text-align: center;
            font-size: 1.8rem;
            padding-top: 1.6rem;
            color: rgba(220, 220, 220, 0.7);
        }

        .recommended-card {
            padding: 1.1rem 1.25rem;
            border-radius: 14px;
            border: 1px solid rgba(30, 136, 229, 0.45);
            background: rgba(30, 136, 229, 0.10);
            margin-bottom: 1rem;
        }

        .recommended-card h3 {
            margin-top: 0;
        }

        .legend-card {
            padding: 0.75rem 0.95rem;
            border-radius: 11px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            margin-bottom: 0.55rem;
            background: rgba(128, 128, 128, 0.045);
        }

        .plain-language {
            padding: 0.8rem 1rem;
            border-left: 4px solid #1976d2;
            background: rgba(25, 118, 210, 0.09);
            border-radius: 8px;
            margin: 0.8rem 0;
        }

        .muted {
            color: rgba(220, 220, 220, 0.70);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Small helpers
# =========================================================


def safe_number(value: Any, default: float = 0.0) -> float:
    """Convert API values safely to a number."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any) -> int:
    return int(round(safe_number(value)))


def money(value: Any) -> str:
    return f"€{safe_number(value):,.0f}"


def percentage(value: Any, decimals: int = 1) -> str:
    return f"{safe_number(value):.{decimals}%}"


def bool_count(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    return int(frame[column].fillna(False).astype(bool).sum())


def numeric_sum(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def metric_card(
    title: str,
    value: str,
    explanation: str,
    icon: str,
    tone: str = "positive",
) -> None:
    safe_title = html.escape(title)
    safe_value = html.escape(value)
    safe_explanation = html.escape(explanation)

    st.markdown(
        f"""
        <div class="simple-card {tone}-card">
            <h3>{icon} {safe_title}</h3>
            <div class="value">{safe_value}</div>
            <div class="explanation">{safe_explanation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False, ttl=60)
def get_api_data(endpoint: str, params: dict) -> Any:
    """Request JSON data from a FastAPI endpoint."""
    response = requests.get(
        f"{API_BASE_URL}/{endpoint}",
        params=params,
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


# =========================================================
# Header
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🛡️ Adaptive Fraud Intelligence</h1>
        <p>
            An operational decision-support system that turns fraud scores into
            prioritised, cost-aware investigations.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Sidebar
# =========================================================

st.sidebar.title("Simulation settings")
st.sidebar.caption(
    "Change the assumptions below to see how the decision system behaves."
)

transaction_limit = st.sidebar.selectbox(
    "Transactions analysed",
    options=[1000, 3000, 10000, 50000],
    index=2,
    help="Number of transactions included in this simulation run.",
)

budget_multiplier = st.sidebar.slider(
    "Alert budget multiplier",
    min_value=1.0,
    max_value=1.5,
    value=1.4,
    step=0.1,
    help=(
        "Controls how many alerts the proposed system may generate relative "
        "to the static-threshold baseline."
    ),
)

analyst_capacity = st.sidebar.number_input(
    "Analyst capacity",
    min_value=1,
    max_value=5000,
    value=250,
    step=50,
    help=(
        "Maximum number of cases that the analyst team can investigate "
        "during the selected period."
    ),
)

with st.sidebar.expander("Advanced settings"):
    investigation_cost = st.number_input(
        "Investigation cost per alert",
        min_value=1.0,
        value=10.0,
        step=1.0,
        help="Estimated cost of investigating one alert.",
    )

    ranking_policy = st.selectbox(
        "Ranking policy",
        options=["risk_zone", "score", "benefit", "hybrid"],
        index=0,
        help="Rule used to order alerts before assigning them to analysts.",
    )

    risk_zone_floor = st.slider(
        "Risk-zone floor",
        min_value=0.0,
        max_value=0.5,
        value=0.3,
        step=0.05,
        help="Minimum model score used by the risk-zone ranking policy.",
    )

if st.sidebar.button("Refresh API data", width="stretch"):
    st.cache_data.clear()

st.sidebar.divider()
st.sidebar.caption(
    "FastAPI expected at `http://127.0.0.1:8001`."
)


# =========================================================
# API parameters and loading
# =========================================================

comparison_params = {
    "limit": int(transaction_limit),
    "investigation_cost": float(investigation_cost),
    "ranking_policy": ranking_policy,
    "risk_zone_floor": float(risk_zone_floor),
    "budget_multiplier": float(budget_multiplier),
}

alerts_params = {
    **comparison_params,
    "analyst_capacity": int(analyst_capacity),
}

curve_params = {
    "limit": int(transaction_limit),
    "investigation_cost": float(investigation_cost),
    "ranking_policy": ranking_policy,
    "risk_zone_floor": float(risk_zone_floor),
}

try:
    with st.spinner("Evaluating the decision system and building the analyst queue..."):
        comparison_data = get_api_data("comparison", comparison_params)
        alerts_data = get_api_data("alerts", alerts_params)
        decision_export_data = get_api_data("decision_export", alerts_params)
        curve_data = get_api_data("operating_curve", curve_params)

except requests.exceptions.ConnectionError:
    st.error(
        "The FastAPI service is not available. Start it in a separate terminal with:\n\n"
        "`py -m uvicorn app.api.main:app --reload --port 8001`"
    )
    st.stop()
except requests.exceptions.Timeout:
    st.error(
        "The API request timed out. Try a smaller transaction limit or restart FastAPI."
    )
    st.stop()
except requests.exceptions.HTTPError as error:
    st.error("FastAPI returned an error. Check the API terminal for details.")
    st.exception(error)
    st.stop()
except requests.exceptions.RequestException as error:
    st.error("An unexpected error occurred while communicating with FastAPI.")
    st.exception(error)
    st.stop()


# =========================================================
# Prepare results
# =========================================================

static_metrics = comparison_data.get("static", {})
decision_metrics = comparison_data.get("decision_system", {})
business_kpis = comparison_data.get("business_kpis", {})

alerts_df = pd.DataFrame(alerts_data)
decision_export_df = pd.DataFrame(decision_export_data)
curve_df = pd.DataFrame(curve_data.get("operating_curve", []))

static_alerts = as_int(static_metrics.get("alerts"))
decision_alerts = as_int(decision_metrics.get("alerts"))
static_frauds = as_int(static_metrics.get("frauds_caught"))
decision_frauds = as_int(decision_metrics.get("frauds_caught"))
static_missed = as_int(static_metrics.get("missed_frauds"))
decision_missed = as_int(decision_metrics.get("missed_frauds"))
static_recall = safe_number(static_metrics.get("recall"))
decision_recall = safe_number(decision_metrics.get("recall"))
static_precision = safe_number(static_metrics.get("precision"))
decision_precision = safe_number(decision_metrics.get("precision"))
static_cost = safe_number(static_metrics.get("total_operational_cost"))
decision_cost = safe_number(decision_metrics.get("total_operational_cost"))

additional_frauds = decision_frauds - static_frauds
additional_alerts = decision_alerts - static_alerts
cost_reduction = static_cost - decision_cost
cost_reduction_pct = cost_reduction / static_cost if static_cost else 0.0
recall_gain = decision_recall - static_recall

selected_for_review = (
    bool_count(decision_export_df, "selected_for_review")
    or len(alerts_df)
)
budget_overflow = bool_count(decision_export_df, "budget_overflow")

if budget_overflow == 0:
    budget_overflow = max(decision_alerts - selected_for_review, 0)


# =========================================================
# Dashboard navigation
# =========================================================

(
    summary_tab,
    why_tab,
    curve_tab,
    queue_tab,
    export_tab,
) = st.tabs(
    [
        "1. Executive Summary",
        "2. Why the system is better",
        "3. Operating Curve",
        "4. Analyst Queue",
        "5. Decision Export",
    ]
)


# =========================================================
# 1. Executive Summary
# =========================================================

with summary_tab:
    st.header("Executive Summary")
    st.caption(
        "The main result in plain language: what improved, by how much, and why it matters."
    )

    st.markdown(
        f"""
        <div class="summary-box">
            <h3>What did the proposed system achieve?</h3>
            <p>• Detected <strong>{additional_frauds:+,} additional fraud cases</strong> compared with the fixed threshold.</p>
            <p>• Increased fraud recall from <strong>{static_recall:.1%}</strong> to <strong>{decision_recall:.1%}</strong>.</p>
            <p>• Reduced total operational cost by <strong>{money(cost_reduction)}</strong> ({cost_reduction_pct:.1%}).</p>
            <p>• Prioritised <strong>{selected_for_review:,}</strong> cases for analysts instead of asking them to review every alert.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card1, card2, card3, card4 = st.columns(4)

    with card1:
        metric_card(
            "Frauds detected",
            f"{decision_frauds:,}",
            f"{additional_frauds:+,} compared with the static threshold.",
            "🛡️",
            "positive",
        )

    with card2:
        metric_card(
            "Fraud recall",
            percentage(decision_recall),
            "Share of all fraud cases successfully detected.",
            "📈",
            "positive",
        )

    with card3:
        metric_card(
            "Operational cost",
            money(decision_cost),
            f"Reduced by {percentage(cost_reduction_pct)} against the baseline.",
            "💰",
            "positive",
        )

    with card4:
        metric_card(
            "Alerts generated",
            f"{decision_alerts:,}",
            f"{additional_alerts:+,} alerts compared with the baseline.",
            "🚨",
            "neutral",
        )

    st.markdown("### What happens to the alerts?")

    wf1, arrow1, wf2, arrow2, wf3 = st.columns([1.25, 0.3, 1.25, 0.3, 1.25])

    with wf1:
        st.markdown(
            f"""
            <div class="workflow-step">
                <div>🚨</div>
                <div class="number">{decision_alerts:,}</div>
                <div class="label">Alerts generated by the decision system</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with arrow1:
        st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)

    with wf2:
        st.markdown(
            f"""
            <div class="workflow-step">
                <div>👩‍💼</div>
                <div class="number">{selected_for_review:,}</div>
                <div class="label">Highest-priority cases assigned to analysts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with arrow2:
        st.markdown('<div class="arrow">+</div>', unsafe_allow_html=True)

    with wf3:
        st.markdown(
            f"""
            <div class="workflow-step">
                <div>⏳</div>
                <div class="number">{budget_overflow:,}</div>
                <div class="label">Alerts outside current analyst capacity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="plain-language">
            <strong>In simple terms:</strong> the model identifies suspicious transactions,
            while the Decision Layer decides which cases are most valuable to investigate first.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Baseline versus proposed system")

    comparison_df = pd.DataFrame(
        [
            {
                "System": "Traditional fixed threshold",
                "Alerts": static_alerts,
                "Frauds detected": static_frauds,
                "Frauds missed": static_missed,
                "Precision": static_precision,
                "Recall": static_recall,
                "Total operational cost": static_cost,
            },
            {
                "System": "Proposed decision system",
                "Alerts": decision_alerts,
                "Frauds detected": decision_frauds,
                "Frauds missed": decision_missed,
                "Precision": decision_precision,
                "Recall": decision_recall,
                "Total operational cost": decision_cost,
            },
        ]
    )

    display_comparison = comparison_df.copy()
    display_comparison["Precision"] = display_comparison["Precision"].map(
        lambda value: f"{value:.2%}"
    )
    display_comparison["Recall"] = display_comparison["Recall"].map(
        lambda value: f"{value:.2%}"
    )
    display_comparison["Total operational cost"] = display_comparison[
        "Total operational cost"
    ].map(lambda value: f"€{value:,.2f}")

    st.dataframe(display_comparison, width="stretch", hide_index=True)

    chart1, chart2 = st.columns(2)

    with chart1:
        st.markdown("#### Detection performance")
        st.bar_chart(
            comparison_df[["System", "Alerts", "Frauds detected"]].set_index(
                "System"
            ),
            width="stretch",
        )

    with chart2:
        st.markdown("#### Operational cost")
        st.bar_chart(
            comparison_df[["System", "Total operational cost"]].set_index(
                "System"
            ),
            width="stretch",
        )

    if business_kpis:
        with st.expander("Technical business-KPI response"):
            st.json(business_kpis)


# =========================================================
# 2. Why the system is better
# =========================================================

with why_tab:
    st.header("Why is the proposed system better?")
    st.caption(
        "The difference is not a new prediction model. The contribution is the Decision Layer placed after the model."
    )

    old_col, new_col = st.columns(2)

    with old_col:
        st.markdown("### Traditional approach")
        st.markdown(
            """
            <div class="simple-card negative-card">
                <h3>Fixed-threshold alerting</h3>
                <p><strong>Fraud score → fixed cut-off → alert or no alert</strong></p>
                <p class="explanation">
                    Every transaction is judged by the same threshold. The process does not
                    directly consider investigation cost, analyst capacity or case priority.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            - Easy to implement, but operationally rigid.
            - Alerts are not automatically ordered by business value.
            - Capacity constraints are handled outside the model.
            - A useful alert can still be missed because of a single fixed cut-off.
            """
        )

    with new_col:
        st.markdown("### Proposed approach")
        st.markdown(
            """
            <div class="simple-card positive-card">
                <h3>Adaptive, cost-aware decisioning</h3>
                <p><strong>Fraud score → ranking → cost evaluation → capacity allocation</strong></p>
                <p class="explanation">
                    The model score is converted into an operational decision using expected
                    value, alert budget and the number of cases analysts can review.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            - Prioritises the most valuable investigations.
            - Explicitly models operational cost.
            - Separates alert generation from analyst assignment.
            - Records cases that exceed available capacity instead of losing them.
            """
        )

    st.markdown("### How the Decision Layer works")

    flow1, flow2, flow3, flow4, flow5 = st.columns(5)
    flow_items = [
        (flow1, "1", "ML score", "Probability that the transaction is fraudulent."),
        (flow2, "2", "Business value", "Potential avoided loss minus investigation cost."),
        (flow3, "3", "Ranking", "Cases are ordered from highest to lowest priority."),
        (flow4, "4", "Capacity", "Only the available number of cases is assigned."),
        (flow5, "5", "Audit trail", "Every decision is exported and can be inspected."),
    ]

    for column, number, title, description in flow_items:
        with column:
            st.markdown(
                f"""
                <div class="workflow-step">
                    <div><strong>Step {number}</strong></div>
                    <div class="number" style="font-size:1.1rem;">{html.escape(title)}</div>
                    <div class="label">{html.escape(description)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Measured improvement")

    improvement1, improvement2, improvement3, improvement4 = st.columns(4)

    with improvement1:
        metric_card(
            "Additional frauds",
            f"{additional_frauds:+,}",
            "Fraud cases detected beyond the static baseline.",
            "➕",
            "positive",
        )

    with improvement2:
        metric_card(
            "Recall improvement",
            f"{recall_gain:+.1%}",
            "Increase in the proportion of all frauds detected.",
            "📈",
            "positive",
        )

    with improvement3:
        metric_card(
            "Cost reduction",
            percentage(cost_reduction_pct),
            "Decrease in total investigation and missed-fraud cost.",
            "💷",
            "positive",
        )

    with improvement4:
        metric_card(
            "Analyst workload",
            f"{selected_for_review:,}",
            "Cases assigned under the selected capacity limit.",
            "👩‍💼",
            "neutral",
        )

    st.info(
        "The model still produces the fraud score. The Decision Layer is responsible "
        "for turning that score into a practical investigation plan."
    )


# =========================================================
# 3. Operating Curve
# =========================================================

with curve_tab:
    st.header("Operating Curve")
    st.caption(
        "The operating curve shows what happens when the organisation allows a larger or smaller alert budget."
    )

    if curve_df.empty:
        st.warning("No operating-curve data were returned by the API.")
    else:
        if "total_operational_cost" in curve_df.columns:
            recommended_row = curve_df.loc[
                pd.to_numeric(
                    curve_df["total_operational_cost"], errors="coerce"
                ).idxmin()
            ]
        else:
            recommended_row = curve_df.iloc[-1]

        recommended_multiplier = safe_number(
            recommended_row.get("budget_multiplier", budget_multiplier)
        )
        recommended_recall = safe_number(recommended_row.get("recall"))
        recommended_alerts = as_int(recommended_row.get("alerts"))
        recommended_frauds = as_int(recommended_row.get("frauds_caught"))
        recommended_cost_reduction = safe_number(
            recommended_row.get("cost_reduction_vs_static")
        )
        recommended_cost_reduction_pct = safe_number(
            recommended_row.get("cost_reduction_pct_vs_static")
        )
        recommended_extra_frauds = as_int(
            recommended_row.get("additional_frauds_caught_vs_static")
        )

        st.markdown(
            f"""
            <div class="recommended-card">
                <h3>⭐ Recommended operating point</h3>
                <p><strong>Budget multiplier:</strong> {recommended_multiplier:.1f}</p>
                <p>✔ Recall: <strong>{recommended_recall:.1%}</strong></p>
                <p>✔ Additional frauds detected: <strong>{recommended_extra_frauds:+,}</strong></p>
                <p>✔ Cost reduction: <strong>{money(recommended_cost_reduction)}</strong> ({recommended_cost_reduction_pct:.1%})</p>
                <p>✔ Alerts generated: <strong>{recommended_alerts:,}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="plain-language">
                <strong>How to read this:</strong> increasing the budget allows more alerts to be investigated.
                This can catch more fraud, but after a certain point the extra alerts stop producing meaningful gains.
            </div>
            """,
            unsafe_allow_html=True,
        )

        graph1, graph2 = st.columns(2)

        with graph1:
            st.markdown("#### Detection improves as the alert budget grows")
            if {"budget_multiplier", "recall"}.issubset(curve_df.columns):
                st.line_chart(
                    curve_df[["budget_multiplier", "recall"]].set_index(
                        "budget_multiplier"
                    ),
                    width="stretch",
                )

        with graph2:
            st.markdown("#### Operational cost across budget levels")
            if {"budget_multiplier", "total_operational_cost"}.issubset(
                curve_df.columns
            ):
                st.line_chart(
                    curve_df[
                        ["budget_multiplier", "total_operational_cost"]
                    ].set_index("budget_multiplier"),
                    width="stretch",
                )

        with st.expander("Show marginal performance table"):
            marginal_columns = [
                "budget_multiplier",
                "additional_alerts_vs_static",
                "additional_frauds_caught_vs_static",
                "cost_reduction_vs_static",
                "cost_reduction_pct_vs_static",
                "marginal_alerts",
                "marginal_frauds_caught",
                "marginal_frauds_per_100_alerts",
            ]
            available_columns = [
                column for column in marginal_columns if column in curve_df.columns
            ]
            marginal_df = curve_df[available_columns].copy()

            st.dataframe(
                marginal_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "budget_multiplier": st.column_config.NumberColumn(
                        "Budget multiplier", format="%.1f"
                    ),
                    "additional_alerts_vs_static": st.column_config.NumberColumn(
                        "Extra alerts vs baseline", format="%d"
                    ),
                    "additional_frauds_caught_vs_static": st.column_config.NumberColumn(
                        "Extra frauds detected", format="%d"
                    ),
                    "cost_reduction_vs_static": st.column_config.NumberColumn(
                        "Cost reduction", format="€%.2f"
                    ),
                    "cost_reduction_pct_vs_static": st.column_config.NumberColumn(
                        "Cost reduction rate", format="%.4f"
                    ),
                    "marginal_alerts": st.column_config.NumberColumn(
                        "New alerts at this step", format="%d"
                    ),
                    "marginal_frauds_caught": st.column_config.NumberColumn(
                        "New frauds at this step", format="%d"
                    ),
                    "marginal_frauds_per_100_alerts": st.column_config.NumberColumn(
                        "New frauds per 100 alerts", format="%.2f"
                    ),
                },
            )

            st.caption(
                "Marginal metrics show the extra benefit obtained when moving from one budget level to the next."
            )

        with st.expander("Show complete operating points"):
            st.dataframe(curve_df, width="stretch", hide_index=True)


# =========================================================
# 4. Analyst Queue
# =========================================================

with queue_tab:
    st.header("Analyst Queue")
    st.caption(
        "The queue converts a large number of alerts into a manageable, prioritised investigation list."
    )

    queue1, queue2, queue3 = st.columns(3)

    with queue1:
        metric_card(
            "Alerts generated",
            f"{decision_alerts:,}",
            "Transactions selected by the adaptive decision system.",
            "🚨",
            "neutral",
        )

    with queue2:
        metric_card(
            "Selected for review",
            f"{selected_for_review:,}",
            "Highest-priority cases assigned to analysts now.",
            "👩‍💼",
            "positive",
        )

    with queue3:
        metric_card(
            "Capacity overflow",
            f"{budget_overflow:,}",
            "Valid alerts that cannot be reviewed under current capacity.",
            "⏳",
            "negative",
        )

    st.markdown(
        f"""
        <div class="plain-language">
            <strong>Workflow:</strong> {decision_alerts:,} alerts were generated →
            {selected_for_review:,} were selected automatically →
            {budget_overflow:,} remain outside the current analyst capacity.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What do the queue columns mean?", expanded=True):
        glossary1, glossary2 = st.columns(2)
        with glossary1:
            st.markdown(
                """
                **Fraud score**  
                Probability assigned by the machine-learning model.

                **Rank score**  
                Priority value used to order investigations.

                **Expected benefit**  
                Estimated financial value of investigating the case.
                """
            )
        with glossary2:
            st.markdown(
                """
                **Queue position**  
                Order in which the analyst should review the case.

                **Selected for review**  
                The case fits within the current analyst capacity.

                **Severity**  
                Human-readable urgency category such as Critical or High.
                """
            )

    if alerts_df.empty:
        st.warning("No alerts were selected for review under the current settings.")
    else:
        queue_frame = alerts_df.copy()

        if "queue_position" in queue_frame.columns:
            queue_frame = queue_frame.sort_values(
                "queue_position", ascending=True, na_position="last"
            )

        st.markdown("### Filter the investigation queue")
        filter1, filter2, filter3 = st.columns(3)

        severity_values = (
            sorted(queue_frame["severity"].dropna().astype(str).unique().tolist())
            if "severity" in queue_frame.columns
            else []
        )
        type_values = (
            sorted(queue_frame["type"].dropna().astype(str).unique().tolist())
            if "type" in queue_frame.columns
            else []
        )

        selected_severities = filter1.multiselect(
            "Severity",
            options=severity_values,
            default=severity_values,
            help="Filter cases by urgency level.",
        )
        selected_types = filter2.multiselect(
            "Transaction type",
            options=type_values,
            default=type_values,
            help="Filter cases by payment or transfer type.",
        )
        minimum_score = filter3.slider(
            "Minimum fraud score",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.01,
            help="Only show cases at or above this model score.",
        )

        filtered_queue = queue_frame.copy()

        if selected_severities and "severity" in filtered_queue.columns:
            filtered_queue = filtered_queue[
                filtered_queue["severity"].isin(selected_severities)
            ]
        if selected_types and "type" in filtered_queue.columns:
            filtered_queue = filtered_queue[
                filtered_queue["type"].isin(selected_types)
            ]
        if "fraud_score" in filtered_queue.columns:
            filtered_queue = filtered_queue[
                pd.to_numeric(filtered_queue["fraud_score"], errors="coerce")
                .fillna(0)
                .ge(minimum_score)
            ]

        queue_columns = [
            "queue_position",
            "selected_for_review",
            "transaction_id",
            "step",
            "type",
            "amount",
            "fraud_score",
            "rank_score",
            "expected_benefit",
            "expected_investigation_cost",
            "severity",
            "analyst_priority",
            "reason",
            "isFraud",
        ]
        visible_queue_columns = [
            column for column in queue_columns if column in filtered_queue.columns
        ]

        st.markdown(f"### Prioritised cases ({len(filtered_queue):,})")
        st.dataframe(
            filtered_queue[visible_queue_columns],
            width="stretch",
            hide_index=True,
            column_config={
                "queue_position": st.column_config.NumberColumn(
                    "Queue position", format="%d", help="Review order."
                ),
                "selected_for_review": st.column_config.CheckboxColumn(
                    "Selected", help="Assigned within current analyst capacity."
                ),
                "amount": st.column_config.NumberColumn("Amount", format="€%.2f"),
                "fraud_score": st.column_config.ProgressColumn(
                    "Fraud score",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.4f",
                    help="Probability assigned by the ML model.",
                ),
                "rank_score": st.column_config.NumberColumn(
                    "Rank score",
                    format="%.4f",
                    help="Priority used to order investigations.",
                ),
                "expected_benefit": st.column_config.NumberColumn(
                    "Expected benefit",
                    format="€%.2f",
                    help="Estimated value of investigating this case.",
                ),
                "expected_investigation_cost": st.column_config.NumberColumn(
                    "Investigation cost", format="€%.2f"
                ),
                "isFraud": st.column_config.CheckboxColumn(
                    "Actual fraud",
                    help="Ground-truth label used only for evaluation.",
                ),
            },
        )

        st.download_button(
            "Download analyst queue as CSV",
            data=filtered_queue.to_csv(index=False).encode("utf-8"),
            file_name="analyst_queue.csv",
            mime="text/csv",
        )


# =========================================================
# 5. Decision Export
# =========================================================

with export_tab:
    st.header("Decision Export")
    st.caption(
        "The export provides a transaction-level audit trail showing how every decision was made."
    )

    st.markdown("### Legend")
    legend1, legend2 = st.columns(2)

    with legend1:
        st.markdown(
            """
            <div class="legend-card"><strong>✓ Static alert</strong><br>
            Selected by the traditional fixed threshold.</div>
            <div class="legend-card"><strong>✓ Adaptive alert</strong><br>
            Selected by the proposed Decision Layer.</div>
            """,
            unsafe_allow_html=True,
        )

    with legend2:
        st.markdown(
            """
            <div class="legend-card"><strong>✓ Selected for review</strong><br>
            Assigned to an analyst within current capacity.</div>
            <div class="legend-card"><strong>✓ Budget overflow</strong><br>
            A valid alert that falls outside current analyst capacity.</div>
            """,
            unsafe_allow_html=True,
        )

    if decision_export_df.empty:
        st.warning("No transaction-level decision records were returned.")
    else:
        export_frame = decision_export_df.copy()

        adaptive_alert_count = numeric_sum(export_frame, "adaptive_alert")
        selected_count = bool_count(export_frame, "selected_for_review")
        overflow_count = bool_count(export_frame, "budget_overflow")
        adaptive_gain_count = numeric_sum(export_frame, "adaptive_gain_fraud")

        export1, export2, export3, export4 = st.columns(4)
        with export1:
            metric_card(
                "Transactions exported",
                f"{len(export_frame):,}",
                "All transactions included in the audit trail.",
                "📦",
                "neutral",
            )
        with export2:
            metric_card(
                "Adaptive alerts",
                f"{adaptive_alert_count:,}",
                "Transactions selected by the proposed system.",
                "🚨",
                "neutral",
            )
        with export3:
            metric_card(
                "Assigned to analysts",
                f"{selected_count:,}",
                "Alerts that fit inside the selected capacity.",
                "👩‍💼",
                "positive",
            )
        with export4:
            metric_card(
                "Outside capacity",
                f"{overflow_count:,}",
                "Alerts retained but not assigned immediately.",
                "⏳",
                "negative",
            )

        st.info(
            f"The proposed system uniquely detected {adaptive_gain_count:,} fraud cases "
            "that were not selected by the static threshold."
        )

        display_option = st.selectbox(
            "Records to display",
            options=[
                "All transactions",
                "Adaptive alerts only",
                "Selected for review",
                "Budget overflow",
                "Adaptive fraud gains",
            ],
            help="Use this filter to inspect a specific decision outcome.",
        )

        filtered_export = export_frame.copy()

        if display_option == "Adaptive alerts only" and "adaptive_alert" in filtered_export:
            filtered_export = filtered_export[
                pd.to_numeric(filtered_export["adaptive_alert"], errors="coerce")
                .fillna(0)
                .eq(1)
            ]
        elif display_option == "Selected for review" and "selected_for_review" in filtered_export:
            filtered_export = filtered_export[
                filtered_export["selected_for_review"].fillna(False).astype(bool)
            ]
        elif display_option == "Budget overflow" and "budget_overflow" in filtered_export:
            filtered_export = filtered_export[
                filtered_export["budget_overflow"].fillna(False).astype(bool)
            ]
        elif display_option == "Adaptive fraud gains" and "adaptive_gain_fraud" in filtered_export:
            filtered_export = filtered_export[
                pd.to_numeric(
                    filtered_export["adaptive_gain_fraud"], errors="coerce"
                )
                .fillna(0)
                .eq(1)
            ]

        export_columns = [
            "transaction_id",
            "step",
            "type",
            "amount",
            "fraud_score",
            "rank_score",
            "expected_benefit",
            "expected_investigation_cost",
            "static_alert",
            "adaptive_alert",
            "adaptive_gain_fraud",
            "selected_for_review",
            "queue_position",
            "budget_overflow",
            "severity",
            "analyst_priority",
            "reason",
            "isFraud",
        ]
        visible_export_columns = [
            column for column in export_columns if column in filtered_export.columns
        ]

        st.markdown(f"### Export preview ({len(filtered_export):,} records)")
        st.dataframe(
            filtered_export[visible_export_columns],
            width="stretch",
            hide_index=True,
            column_config={
                "amount": st.column_config.NumberColumn("Amount", format="€%.2f"),
                "fraud_score": st.column_config.ProgressColumn(
                    "Fraud score",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.4f",
                    help="Probability assigned by the ML model.",
                ),
                "rank_score": st.column_config.NumberColumn(
                    "Rank score", format="%.4f"
                ),
                "expected_benefit": st.column_config.NumberColumn(
                    "Expected benefit", format="€%.2f"
                ),
                "expected_investigation_cost": st.column_config.NumberColumn(
                    "Investigation cost", format="€%.2f"
                ),
                "static_alert": st.column_config.CheckboxColumn("Static alert"),
                "adaptive_alert": st.column_config.CheckboxColumn("Adaptive alert"),
                "adaptive_gain_fraud": st.column_config.CheckboxColumn(
                    "Adaptive fraud gain"
                ),
                "selected_for_review": st.column_config.CheckboxColumn(
                    "Selected for review"
                ),
                "queue_position": st.column_config.NumberColumn(
                    "Queue position", format="%d"
                ),
                "budget_overflow": st.column_config.CheckboxColumn(
                    "Budget overflow"
                ),
                "isFraud": st.column_config.CheckboxColumn("Actual fraud"),
            },
        )

        st.download_button(
            "Download decision export as CSV",
            data=filtered_export.to_csv(index=False).encode("utf-8"),
            file_name="decision_export.csv",
            mime="text/csv",
        )


# =========================================================
# Footer
# =========================================================

st.divider()
st.caption(
    "Fraud Detection Decision System — adaptive, cost-aware and analyst-capacity-aware alerting."
)