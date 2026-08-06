import pandas as pd
import requests
import streamlit as st


# =========================================================
# Configuration
# =========================================================

# Το FastAPI τρέχει στη θύρα 8001.
# Αν αργότερα χρησιμοποιήσεις ξανά την 8000, άλλαξε μόνο αυτή τη γραμμή.
API_BASE_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Adaptive Fraud Intelligence",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Adaptive Fraud Intelligence")

st.caption(
    "Static threshold versus budget-aware, cost-aware "
    "fraud alert selection and analyst prioritisation."
)


# =========================================================
# Sidebar
# =========================================================

st.sidebar.title("Simulation Settings")

transaction_limit = st.sidebar.selectbox(
    "Transaction limit",
    options=[1000, 3000, 10000, 50000],
    index=2,
)

budget_multiplier = st.sidebar.slider(
    "Alert budget multiplier",
    min_value=1.0,
    max_value=1.5,
    value=1.4,
    step=0.1,
)

analyst_capacity = st.sidebar.number_input(
    "Analyst capacity",
    min_value=1,
    max_value=5000,
    value=250,
    step=50,
    help=(
        "Maximum number of prioritised alerts that analysts "
        "can investigate during the selected period."
    ),
)

with st.sidebar.expander("Advanced settings"):
    investigation_cost = st.number_input(
        "Investigation cost per alert",
        min_value=1.0,
        value=10.0,
        step=1.0,
    )

    ranking_policy = st.selectbox(
        "Ranking policy",
        options=[
            "risk_zone",
            "score",
            "benefit",
            "hybrid",
        ],
        index=0,
    )

    risk_zone_floor = st.slider(
        "Risk-zone floor",
        min_value=0.0,
        max_value=0.5,
        value=0.3,
        step=0.05,
    )

if st.sidebar.button(
    "Refresh API data",
    width="stretch",
):
    st.cache_data.clear()


# =========================================================
# API helpers
# =========================================================

@st.cache_data(
    show_spinner=False,
    ttl=60,
)
def get_api_data(
    endpoint: str,
    params: dict,
):
    """
    Request JSON data from a FastAPI endpoint.
    """
    response = requests.get(
        f"{API_BASE_URL}/{endpoint}",
        params=params,
        timeout=180,
    )

    response.raise_for_status()

    return response.json()


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



# =========================================================
# Load API data
# =========================================================

try:
    with st.spinner(
        "Running decision-system evaluation and building analyst queue..."
    ):
        comparison_data = get_api_data(
            endpoint="comparison",
            params=comparison_params,
        )

        alerts_data = get_api_data(
            endpoint="alerts",
            params=alerts_params,
        )

        decision_export_data = get_api_data(
            endpoint="decision_export",
            params=alerts_params,
        )

        curve_data = get_api_data(
            endpoint="operating_curve",
            params=curve_params,
        )

except requests.exceptions.ConnectionError:
    st.error(
        "The FastAPI service is not available at "
        f"`{API_BASE_URL}`.\n\n"
        "Start it in a separate terminal with:\n\n"
        "`py -m uvicorn app.api.main:app --reload --port 8001`"
    )
    st.stop()

except requests.exceptions.Timeout:
    st.error(
        "The API request timed out. Try a smaller transaction limit "
        "or restart the FastAPI service."
    )
    st.stop()

except requests.exceptions.HTTPError as error:
    st.error(
        "The FastAPI service returned an error. "
        "Check the API terminal for more information."
    )
    st.exception(error)
    st.stop()

except requests.exceptions.RequestException as error:
    st.error(
        "An unexpected error occurred while communicating with FastAPI."
    )
    st.exception(error)
    st.stop()


# =========================================================
# Prepare API results
# =========================================================

static_metrics = comparison_data["static"]
decision_metrics = comparison_data["decision_system"]
business_kpis = comparison_data.get("business_kpis", {})

alerts_df = pd.DataFrame(alerts_data)
decision_export_df = pd.DataFrame(decision_export_data)

curve_df = pd.DataFrame(
    curve_data.get(
        "operating_curve",
        [],
    )
)

comparison_df = pd.DataFrame(
    [
        {
            "System": "Static threshold",
            "Alerts": static_metrics["alerts"],
            "Frauds caught": static_metrics["frauds_caught"],
            "Missed frauds": static_metrics["missed_frauds"],
            "Precision": static_metrics["precision"],
            "Recall": static_metrics["recall"],
            "Investigation cost": static_metrics[
                "investigation_cost_total"
            ],
            "Missed fraud cost": static_metrics[
                "missed_fraud_cost"
            ],
            "Total operational cost": static_metrics[
                "total_operational_cost"
            ],
        },
        {
            "System": "Budget-aware decision system",
            "Alerts": decision_metrics["alerts"],
            "Frauds caught": decision_metrics["frauds_caught"],
            "Missed frauds": decision_metrics["missed_frauds"],
            "Precision": decision_metrics["precision"],
            "Recall": decision_metrics["recall"],
            "Investigation cost": decision_metrics[
                "investigation_cost_total"
            ],
            "Missed fraud cost": decision_metrics[
                "missed_fraud_cost"
            ],
            "Total operational cost": decision_metrics[
                "total_operational_cost"
            ],
        },
    ]
)


# =========================================================
# Dashboard tabs
# =========================================================

(
    overview_tab,
    curve_tab,
    queue_tab,
    export_tab,
) = st.tabs(
    [
        "Executive Overview",
        "Operating Curve",
        "Analyst Queue",
        "Decision Export",
    ]
)


# =========================================================
# Executive Overview
# =========================================================

with overview_tab:
    st.subheader(
        "Static threshold vs budget-aware decision system"
    )

    recall_delta = (
        decision_metrics["recall"]
        - static_metrics["recall"]
    )

    precision_delta = (
        decision_metrics["precision"]
        - static_metrics["precision"]
    )

    frauds_delta = (
        decision_metrics["frauds_caught"]
        - static_metrics["frauds_caught"]
    )

    alerts_delta = (
        decision_metrics["alerts"]
        - static_metrics["alerts"]
    )

    cost_delta = (
        decision_metrics["total_operational_cost"]
        - static_metrics["total_operational_cost"]
    )

    cost_reduction = (
        static_metrics["total_operational_cost"]
        - decision_metrics["total_operational_cost"]
    )

    if static_metrics["total_operational_cost"] > 0:
        cost_reduction_pct = (
            cost_reduction
            / static_metrics["total_operational_cost"]
        )
    else:
        cost_reduction_pct = 0.0

    metric_col1, metric_col2, metric_col3, metric_col4 = (
        st.columns(4)
    )

    metric_col1.metric(
        label="Decision-system recall",
        value=f"{decision_metrics['recall']:.1%}",
        delta=f"{recall_delta:+.1%}",
    )

    metric_col2.metric(
        label="Frauds caught",
        value=f"{decision_metrics['frauds_caught']:,}",
        delta=f"{frauds_delta:+,}",
    )

    metric_col3.metric(
        label="Alerts generated",
        value=f"{decision_metrics['alerts']:,}",
        delta=f"{alerts_delta:+,}",
    )

    metric_col4.metric(
        label="Total operational cost",
        value=(
            f"€{decision_metrics['total_operational_cost']:,.0f}"
        ),
        delta=f"€{cost_delta:+,.0f}",
        delta_color="inverse",
    )

    st.markdown("### Business impact")

    business_col1, business_col2, business_col3, business_col4 = (
        st.columns(4)
    )

    business_col1.metric(
        label="Cost reduction",
        value=f"€{cost_reduction:,.0f}",
    )

    business_col2.metric(
        label="Cost reduction percentage",
        value=f"{cost_reduction_pct:.1%}",
    )

    business_col3.metric(
        label="Precision change",
        value=f"{precision_delta:+.2%}",
    )

    business_col4.metric(
        label="Analyst capacity",
        value=f"{int(analyst_capacity):,}",
    )

    if business_kpis:
        with st.expander(
            "View business KPI response",
            expanded=False,
        ):
            st.json(business_kpis)

    st.markdown("### Core comparison")

    display_comparison_df = comparison_df.copy()

    percentage_columns = [
        "Precision",
        "Recall",
    ]

    money_columns = [
        "Investigation cost",
        "Missed fraud cost",
        "Total operational cost",
    ]

    for column in percentage_columns:
        display_comparison_df[column] = (
            display_comparison_df[column].map(
                lambda value: f"{value:.2%}"
            )
        )

    for column in money_columns:
        display_comparison_df[column] = (
            display_comparison_df[column].map(
                lambda value: f"€{value:,.2f}"
            )
        )

    st.dataframe(
        display_comparison_df,
        width="stretch",
        hide_index=True,
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### Alerts and frauds caught")

        alerts_frauds_chart = comparison_df[
            [
                "System",
                "Alerts",
                "Frauds caught",
            ]
        ].set_index("System")

        st.bar_chart(
            alerts_frauds_chart,
            width="stretch",
        )

    with chart_col2:
        st.markdown("### Total operational cost")

        cost_chart = comparison_df[
            [
                "System",
                "Total operational cost",
            ]
        ].set_index("System")

        st.bar_chart(
            cost_chart,
            width="stretch",
        )

    st.caption(
        "The decision layer ranks transactions according to "
        "operational value and selects alerts within the "
        "available alert budget."
    )


# =========================================================
# Operating Curve
# =========================================================

with curve_tab:
    st.subheader("Alert-budget operating curve")

    st.caption(
        "The operating curve evaluates how fraud detection, "
        "alert volume and operational cost change across "
        "different budget multipliers."
    )

    if curve_df.empty:
        st.warning(
            "No operating-curve data were returned by the API."
        )

    else:
        required_cost_column = (
            "total_operational_cost"
            in curve_df.columns
        )

        if required_cost_column:
            best_row = curve_df.loc[
                curve_df[
                    "total_operational_cost"
                ].idxmin()
            ]

            st.info(
                "Lowest-cost operating point: "
                f"budget multiplier "
                f"{best_row['budget_multiplier']:.1f}, "
                f"recall {best_row['recall']:.1%}, "
                f"{int(best_row['alerts']):,} alerts and "
                f"total operational cost "
                f"€{best_row['total_operational_cost']:,.0f}."
            )

        curve_col1, curve_col2 = st.columns(2)

        with curve_col1:
            st.markdown(
                "### Budget multiplier → Recall"
            )

            recall_curve = curve_df[
                [
                    "budget_multiplier",
                    "recall",
                ]
            ].set_index("budget_multiplier")

            st.line_chart(
                recall_curve,
                width="stretch",
            )

        with curve_col2:
            st.markdown(
                "### Budget multiplier → Operational cost"
            )

            if required_cost_column:
                cost_curve = curve_df[
                    [
                        "budget_multiplier",
                        "total_operational_cost",
                    ]
                ].set_index("budget_multiplier")

                st.line_chart(
                    cost_curve,
                    width="stretch",
                )
            else:
                st.warning(
                    "The operational-cost column is missing."
                )

        st.markdown("### Marginal performance")

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

        available_marginal_columns = [
            column
            for column in marginal_columns
            if column in curve_df.columns
        ]

        if available_marginal_columns:
            marginal_df = curve_df[
                available_marginal_columns
            ].copy()

            marginal_column_names = {
                "budget_multiplier": "Budget multiplier",
                "additional_alerts_vs_static": (
                    "Additional alerts vs static"
                ),
                "additional_frauds_caught_vs_static": (
                    "Additional frauds caught vs static"
                ),
                "cost_reduction_vs_static": (
                    "Cost reduction vs static"
                ),
                "cost_reduction_pct_vs_static": (
                    "Cost reduction percentage"
                ),
                "marginal_alerts": "Marginal alerts",
                "marginal_frauds_caught": (
                    "Marginal frauds caught"
                ),
                "marginal_frauds_per_100_alerts": (
                    "Marginal frauds per 100 alerts"
                ),
            }

            marginal_df = marginal_df.rename(
                columns=marginal_column_names
            )

            if (
                "Cost reduction vs static"
                in marginal_df.columns
            ):
                marginal_df[
                    "Cost reduction vs static"
                ] = marginal_df[
                    "Cost reduction vs static"
                ].map(
                    lambda value: f"€{value:,.2f}"
                )

            if (
                "Cost reduction percentage"
                in marginal_df.columns
            ):
                marginal_df[
                    "Cost reduction percentage"
                ] = marginal_df[
                    "Cost reduction percentage"
                ].map(
                    lambda value: f"{value:.2%}"
                )

            st.dataframe(
                marginal_df,
                width="stretch",
                hide_index=True,
            )

        st.markdown("### Complete operating points")

        preferred_curve_columns = [
            "budget_multiplier",
            "decision_budget",
            "alerts",
            "frauds_caught",
            "missed_frauds",
            "precision",
            "recall",
            "total_operational_cost",
            "additional_alerts_vs_static",
            "additional_frauds_caught_vs_static",
            "cost_reduction_vs_static",
            "cost_reduction_pct_vs_static",
            "marginal_alerts",
            "marginal_frauds_caught",
            "marginal_frauds_per_100_alerts",
        ]

        available_curve_columns = [
            column
            for column in preferred_curve_columns
            if column in curve_df.columns
        ]

        operating_table = curve_df[
            available_curve_columns
        ].copy()

        st.dataframe(
            operating_table,
            width="stretch",
            hide_index=True,
            column_config={
                "budget_multiplier": (
                    st.column_config.NumberColumn(
                        "Budget multiplier",
                        format="%.1f",
                    )
                ),
                "decision_budget": (
                    st.column_config.NumberColumn(
                        "Decision budget",
                        format="%d",
                    )
                ),
                "precision": (
                    st.column_config.NumberColumn(
                        "Precision",
                        format="%.4f",
                    )
                ),
                "recall": (
                    st.column_config.NumberColumn(
                        "Recall",
                        format="%.4f",
                    )
                ),
                "total_operational_cost": (
                    st.column_config.NumberColumn(
                        "Total operational cost",
                        format="€%.2f",
                    )
                ),
                "cost_reduction_vs_static": (
                    st.column_config.NumberColumn(
                        "Cost reduction vs static",
                        format="€%.2f",
                    )
                ),
                "cost_reduction_pct_vs_static": (
                    st.column_config.NumberColumn(
                        "Cost reduction percentage",
                        format="%.4f",
                    )
                ),
                "marginal_frauds_per_100_alerts": (
                    st.column_config.NumberColumn(
                        "Marginal frauds per 100 alerts",
                        format="%.2f",
                    )
                ),
            },
        )


# =========================================================
# Analyst Queue
# =========================================================

with queue_tab:
    st.subheader(
        "Prioritised analyst investigation queue"
    )

    st.caption(
        "This queue is produced by `analyst_queue_service.py` "
        "through the `/alerts` endpoint. Only transactions "
        "selected within the analyst capacity are displayed."
    )

    if alerts_df.empty:
        st.warning(
            "No alerts were selected for analyst review "
            "under the current settings."
        )

    else:
        alerts_df = alerts_df.copy()

        if "queue_position" in alerts_df.columns:
            alerts_df = alerts_df.sort_values(
                by="queue_position",
                ascending=True,
            ).reset_index(drop=True)

        selected_count = (
            int(
                alerts_df[
                    "selected_for_review"
                ].fillna(False).astype(bool).sum()
            )
            if "selected_for_review" in alerts_df.columns
            else len(alerts_df)
        )

        critical_count = (
            int(
                (
                    alerts_df["severity"] == "CRITICAL"
                ).sum()
            )
            if "severity" in alerts_df.columns
            else 0
        )

        high_count = (
            int(
                (
                    alerts_df["severity"] == "HIGH"
                ).sum()
            )
            if "severity" in alerts_df.columns
            else 0
        )

        fraud_count = (
            int(alerts_df["isFraud"].sum())
            if "isFraud" in alerts_df.columns
            else 0
        )

        queue_metric1, queue_metric2, queue_metric3, queue_metric4 = (
            st.columns(4)
        )

        queue_metric1.metric(
            label="Analyst capacity",
            value=f"{int(analyst_capacity):,}",
        )

        queue_metric2.metric(
            label="Selected for review",
            value=f"{selected_count:,}",
        )

        queue_metric3.metric(
            label="Critical / high alerts",
            value=f"{critical_count + high_count:,}",
        )

        queue_metric4.metric(
            label="Confirmed frauds in queue",
            value=f"{fraud_count:,}",
        )

        st.markdown("### Queue filters")

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        severity_options = (
            sorted(
                alerts_df["severity"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if "severity" in alerts_df.columns
            else []
        )

        selected_severities = filter_col1.multiselect(
            label="Severity",
            options=severity_options,
            default=severity_options,
        )

        transaction_types = (
            sorted(
                alerts_df["type"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if "type" in alerts_df.columns
            else []
        )

        selected_types = filter_col2.multiselect(
            label="Transaction type",
            options=transaction_types,
            default=transaction_types,
        )

        minimum_fraud_score = filter_col3.slider(
            label="Minimum fraud score",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.01,
        )

        filtered_queue_df = alerts_df.copy()

        if (
            selected_severities
            and "severity" in filtered_queue_df.columns
        ):
            filtered_queue_df = filtered_queue_df[
                filtered_queue_df["severity"].isin(
                    selected_severities
                )
            ]

        if (
            selected_types
            and "type" in filtered_queue_df.columns
        ):
            filtered_queue_df = filtered_queue_df[
                filtered_queue_df["type"].isin(
                    selected_types
                )
            ]

        if "fraud_score" in filtered_queue_df.columns:
            filtered_queue_df = filtered_queue_df[
                filtered_queue_df["fraud_score"]
                >= minimum_fraud_score
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

        available_queue_columns = [
            column
            for column in queue_columns
            if column in filtered_queue_df.columns
        ]

        st.markdown(
            f"### Investigation queue "
            f"({len(filtered_queue_df):,} records)"
        )

        st.dataframe(
            filtered_queue_df[
                available_queue_columns
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "queue_position": (
                    st.column_config.NumberColumn(
                        "Queue position",
                        format="%d",
                    )
                ),
                "selected_for_review": (
                    st.column_config.CheckboxColumn(
                        "Selected for review"
                    )
                ),
                "transaction_id": (
                    st.column_config.TextColumn(
                        "Transaction ID"
                    )
                ),
                "amount": (
                    st.column_config.NumberColumn(
                        "Amount",
                        format="€%.2f",
                    )
                ),
                "fraud_score": (
                    st.column_config.ProgressColumn(
                        "Fraud score",
                        min_value=0.0,
                        max_value=1.0,
                        format="%.4f",
                    )
                ),
                "rank_score": (
                    st.column_config.NumberColumn(
                        "Rank score",
                        format="%.4f",
                    )
                ),
                "expected_benefit": (
                    st.column_config.NumberColumn(
                        "Expected benefit",
                        format="€%.2f",
                    )
                ),
                "expected_investigation_cost": (
                    st.column_config.NumberColumn(
                        "Investigation cost",
                        format="€%.2f",
                    )
                ),
                "isFraud": (
                    st.column_config.CheckboxColumn(
                        "Actual fraud"
                    )
                ),
            },
        )

        queue_csv = filtered_queue_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download analyst queue as CSV",
            data=queue_csv,
            file_name="analyst_queue.csv",
            mime="text/csv",
        )


# =========================================================
# Decision Export
# =========================================================

with export_tab:
    st.subheader(
        "Transaction-level decision export"
    )

    st.caption(
        "The `/decision_export` endpoint includes static and "
        "adaptive decisions, analyst selection, queue position "
        "and budget-overflow information."
    )

    if decision_export_df.empty:
        st.warning(
            "No transaction-level decision records were returned."
        )

    else:
        decision_export_df = decision_export_df.copy()

        total_transactions = len(decision_export_df)

        adaptive_alert_count = (
            int(
                decision_export_df[
                    "adaptive_alert"
                ].sum()
            )
            if "adaptive_alert"
            in decision_export_df.columns
            else 0
        )

        selected_review_count = (
            int(
                decision_export_df[
                    "selected_for_review"
                ].fillna(False).astype(bool).sum()
            )
            if "selected_for_review"
            in decision_export_df.columns
            else 0
        )

        overflow_count = (
            int(
                decision_export_df[
                    "budget_overflow"
                ].fillna(False).astype(bool).sum()
            )
            if "budget_overflow"
            in decision_export_df.columns
            else 0
        )

        adaptive_gain_count = (
            int(
                decision_export_df[
                    "adaptive_gain_fraud"
                ].sum()
            )
            if "adaptive_gain_fraud"
            in decision_export_df.columns
            else 0
        )

        export_metric1, export_metric2, export_metric3, export_metric4 = (
            st.columns(4)
        )

        export_metric1.metric(
            label="Exported transactions",
            value=f"{total_transactions:,}",
        )

        export_metric2.metric(
            label="Adaptive alerts",
            value=f"{adaptive_alert_count:,}",
        )

        export_metric3.metric(
            label="Selected for review",
            value=f"{selected_review_count:,}",
        )

        export_metric4.metric(
            label="Budget overflow",
            value=f"{overflow_count:,}",
        )

        st.info(
            f"The adaptive system uniquely captured "
            f"{adaptive_gain_count:,} fraud cases that were "
            f"not selected by the static threshold."
        )

        st.markdown("### Analyst-capacity allocation")

        capacity_summary_df = pd.DataFrame(
            [
                {
                    "Category": "Selected for review",
                    "Transactions": selected_review_count,
                },
                {
                    "Category": "Budget overflow",
                    "Transactions": overflow_count,
                },
            ]
        ).set_index("Category")

        st.bar_chart(
            capacity_summary_df,
            width="stretch",
        )

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

        available_export_columns = [
            column
            for column in export_columns
            if column in decision_export_df.columns
        ]

        export_filter = st.selectbox(
            label="Display records",
            options=[
                "All transactions",
                "Adaptive alerts only",
                "Selected for review",
                "Budget overflow",
                "Adaptive fraud gains",
            ],
        )

        filtered_export_df = decision_export_df.copy()

        if (
            export_filter == "Adaptive alerts only"
            and "adaptive_alert"
            in filtered_export_df.columns
        ):
            filtered_export_df = filtered_export_df[
                filtered_export_df[
                    "adaptive_alert"
                ] == 1
            ]

        elif (
            export_filter == "Selected for review"
            and "selected_for_review"
            in filtered_export_df.columns
        ):
            filtered_export_df = filtered_export_df[
                filtered_export_df[
                    "selected_for_review"
                ].fillna(False).astype(bool)
            ]

        elif (
            export_filter == "Budget overflow"
            and "budget_overflow"
            in filtered_export_df.columns
        ):
            filtered_export_df = filtered_export_df[
                filtered_export_df[
                    "budget_overflow"
                ].fillna(False).astype(bool)
            ]

        elif (
            export_filter == "Adaptive fraud gains"
            and "adaptive_gain_fraud"
            in filtered_export_df.columns
        ):
            filtered_export_df = filtered_export_df[
                filtered_export_df[
                    "adaptive_gain_fraud"
                ] == 1
            ]

        st.markdown(
            f"### Export preview "
            f"({len(filtered_export_df):,} records)"
        )

        st.dataframe(
            filtered_export_df[
                available_export_columns
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "amount": (
                    st.column_config.NumberColumn(
                        "Amount",
                        format="€%.2f",
                    )
                ),
                "fraud_score": (
                    st.column_config.ProgressColumn(
                        "Fraud score",
                        min_value=0.0,
                        max_value=1.0,
                        format="%.4f",
                    )
                ),
                "rank_score": (
                    st.column_config.NumberColumn(
                        "Rank score",
                        format="%.4f",
                    )
                ),
                "expected_benefit": (
                    st.column_config.NumberColumn(
                        "Expected benefit",
                        format="€%.2f",
                    )
                ),
                "expected_investigation_cost": (
                    st.column_config.NumberColumn(
                        "Investigation cost",
                        format="€%.2f",
                    )
                ),
                "static_alert": (
                    st.column_config.CheckboxColumn(
                        "Static alert"
                    )
                ),
                "adaptive_alert": (
                    st.column_config.CheckboxColumn(
                        "Adaptive alert"
                    )
                ),
                "adaptive_gain_fraud": (
                    st.column_config.CheckboxColumn(
                        "Adaptive fraud gain"
                    )
                ),
                "selected_for_review": (
                    st.column_config.CheckboxColumn(
                        "Selected for review"
                    )
                ),
                "queue_position": (
                    st.column_config.NumberColumn(
                        "Queue position",
                        format="%d",
                    )
                ),
                "budget_overflow": (
                    st.column_config.CheckboxColumn(
                        "Budget overflow"
                    )
                ),
                "isFraud": (
                    st.column_config.CheckboxColumn(
                        "Actual fraud"
                    )
                ),
            },
        )

        export_csv = filtered_export_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download decision export as CSV",
            data=export_csv,
            file_name="decision_export.csv",
            mime="text/csv",
        )


# =========================================================
# Footer
# =========================================================

st.divider()

st.caption(
    "Fraud Detection Decision System — adaptive, "
    "cost-aware and analyst-capacity-aware alerting."
)