Adaptive Fraud Intelligence







Decision-Centric Fraud Detection Framework for Adaptive Alert Selection, Analyst Prioritisation, Sequential Evaluation, Cost-Aware Decision Support, and Operational Monitoring

Research prototype: evaluated on the synthetic PaySim mobile-money dataset through offline chronological replay. It does not process live banking or UPI transactions. Identifiers shown by the application are simulation identifiers and do not represent real customers, cards, accounts, or payment identifiers.

Overview

Traditional fraud-detection projects often stop after producing a fraud probability. This project focuses on the operational question that follows:

Which suspicious transactions should be investigated when analyst capacity is limited?

The framework separates fraud prediction from fraud-response decision making. A machine-learning model generates fraud-risk estimates; a dedicated decision layer then creates candidate alerts, suppresses repeated alerts, prioritises eligible cases, and applies per-step analyst-capacity constraints.

The result is a research-oriented Fraud Decision Support System (DSS) rather than a prediction-only dashboard.

Research Contribution

The framework integrates:

machine-learning fraud scoring;

Static and Adaptive alert-selection policies;

adaptive candidate-alert budgeting;

operational priority ranking;

repeat-alert suppression;

per-step analyst capacity;

prioritised investigation queues;

transaction-level decision explanations;

sequential chronological replay;

operational monitoring;

cost-aware evaluation; and

controlled sensitivity analysis.

The central idea is:

Fraud score
    ↓
Alert-selection policy
    ↓
Candidate alert
    ↓
Suppression
    ↓
Priority ranking
    ↓
Analyst capacity
    ↓
Investigation decision
    ↓
Operational evaluation

Static vs Adaptive Policies

Static

The Static policy uses a fixed fraud-risk threshold. Transactions reaching the configured threshold become candidate alerts.

Adaptive

The Adaptive policy combines:

a minimum Adaptive fraud threshold, which defines the minimum fraud risk required for consideration; and

an Adaptive candidate-alert budget, controlled relative to the Static baseline alert volume by the budget multiplier.

Both policies subsequently pass through the same sequential operational constraints.

Fraud risk is not rank score

Fraud risk answers:

How likely does the ML model think this transaction is fraud?

It is a calibrated model probability.

Rank score answers:

How important is it to investigate this eligible alert relative to the others?

It is an operational priority value used for ordering alerts and is not a probability.

Sequential Operational Evaluation

The primary operational evaluation is an offline chronological replay, not a deployed live transaction stream.

Transactions are processed in PaySim step order. Transactions sharing the same step form one operational decision cycle.

Within each step:

transactions arrive;

fraud risk is calculated;

Static or Adaptive logic creates candidate alerts;

repeated alerts may be suppressed;

eligible alerts are prioritised;

analyst capacity is applied; and

investigated alerts are retrospectively compared with PaySim fraud labels.

Unused analyst capacity is not carried into the next step.

The backend validates the accounting identity:

Candidate alerts
= Investigated alerts
+ Suppressed alerts
+ Capacity-rejected alerts

Machine-Learning Layer

The predictive component uses a scikit-learn pipeline centred on Logistic Regression.

Core PaySim variables

step

type

amount

oldbalanceOrg

newbalanceOrig

oldbalanceDest

newbalanceDest

isFraud — evaluation target

Identifiers and isFlaggedFraud are excluded from predictive modelling.

Engineered features

log_amount

origin_balance_error

destination_balance_error

abs_origin_balance_error

abs_destination_balance_error

Numeric and categorical variables are handled through the preprocessing pipeline, and calibrated fraud probabilities can be passed to the decision layer.

System Architecture

flowchart TD
    A[PaySim transactions] --> B[Feature engineering]
    B --> C[Fraud detection model]
    C --> D[Calibrated fraud-risk score]
    D --> E{Decision policy}
    E -->|Static| F[Fixed threshold]
    E -->|Adaptive| G[Minimum threshold + candidate budget]
    F --> H[Candidate alerts]
    G --> H
    H --> I[Repeat-alert suppression]
    I --> J[Priority ranking]
    J --> K[Per-step analyst capacity]
    K --> L[Investigated alerts]
    K --> M[Capacity-rejected alerts]
    L --> N[Operational evaluation]
    M --> N
    N --> O[Monitoring + sensitivity analysis]
    O --> P[FastAPI]
    P --> Q[Streamlit dashboard]

Dashboard

The Streamlit dashboard uses progressive disclosure: high-level decision information is shown first, while methodological and technical detail remains available for deeper inspection.

1. Executive Summary

Provides the current Static vs Adaptive comparison:

recommended policy;

investigated alerts;

frauds detected and missed;

precision and recall;

estimated operational cost; and

management interpretation.

The ideal Batch result is retained only as a methodological reference. The Sequential replay is the primary operational evaluation.

2. Analyst Capacity

Explains how candidate alerts reach—or fail to reach—the analyst queue.

It includes:

investigated alerts;

suppressed alerts;

capacity-rejected alerts;

Fraud Investigation Funnel;

capacity by operational step;

fraud risk by transaction type;

full Prioritised Investigation Queue; and

transaction-level Alert Decision Explanation.

The queue includes investigated and non-investigated candidates so the capacity cutoff remains inspectable.

3. Sequential Workflow

Documents the seven-stage decision process and explicitly distinguishes the implementation from a true production real-time system.

Correct terminology:

Offline sequential simulation / chronological replay with real-time-oriented decision cycles.

4. Monitoring

Monitoring windows summarise consecutive transaction blocks for reporting. They are distinct from operational PaySim steps.

The dashboard tracks:

candidate alerts;

investigated alerts;

capacity overflow;

frauds missed;

recall; and

simulation-based estimated operational cost.

5. Sensitivity Analysis

Seven operating parameters are tested while changing one parameter at a time:

Parameter

Tested values

Transaction volume

1,000 · 3,000 · 10,000

Analyst capacity

10–100 alerts per operational step

Investigation cost

€5 · €10 · €15 · €20 · €25

Suppression window

0 · 1 · 2 · 3 · 5 steps

Adaptive budget multiplier

1.0–2.0

Static fraud threshold

0.30 · 0.40 · 0.50 · 0.60 · 0.70

Minimum Adaptive fraud threshold

0.10 · 0.20 · 0.30 · 0.40 · 0.50

The sensitivity interface includes:

Decision Scenario Explorer;

baseline configuration;

summary results across all tested settings;

full comparison evidence;

experiment-specific drill-down; and

interpretation of when Adaptive, Static, or neither policy is clearly preferable.

Current Baseline Result

For the current 10,000-transaction Sequential scenario with analyst capacity of 50 alerts per operational step:

Metric

Static

Adaptive

Investigated alerts

313

349

Frauds detected

27

30

Frauds missed

41

38

Precision

8.6%

8.6%

Recall

39.7%

44.1%

Estimated operational cost

€1,745,391.01

€1,726,843.29

Under this configuration, Adaptive achieves approximately:

+4.4 percentage points recall

+3 frauds detected

€18,547.72 lower estimated operational cost

These are simulation-based estimates, not observed banking losses.

The sensitivity results also show that Adaptive is not universally superior. Its advantage depends on alert-selection strategy, analyst capacity, thresholds, suppression, workload, and other operating assumptions.

Example Decision Scenario

Changing Adaptive analyst capacity from 50 to 60 alerts per operational step gives:

Outcome

50/step

60/step

Candidate alerts

1,020

1,020

Investigated alerts

349

402

Frauds detected

30

32

Recall

44.1%

47.1%

Suppressed alerts

21

26

Capacity-rejected alerts

650

592

This illustrates the purpose of the DSS: operational parameters can be evaluated in terms of fraud coverage, workload, overflow, and estimated cost rather than model accuracy alone.

Dataset, Privacy, and Scope

The project uses the PaySim synthetic financial transaction dataset.

No real customer, card, bank-account, UPI, or payment identifiers are required. Dashboard transaction IDs and entity references are simulation identifiers.

The dataset is not included in the repository and is expected locally at:

data/raw/AIML Dataset.csv

Synthetic data is an explicit research limitation. Results should not be interpreted as validated production performance on a real financial institution's transaction stream.

Model Persistence and Deployment

The trained model should be loaded from a persisted/versioned model artifact rather than depending on in-memory training history.

This is important for containerised deployment because process memory and runtime files may be ephemeral after restart.

Required model artifacts, configuration, and registry information should therefore be available from version-controlled or otherwise persistent storage whenever the application starts.

Technologies

Machine Learning & Data

Python

Pandas

NumPy

scikit-learn

Matplotlib

Joblib

Application

FastAPI

Streamlit

REST APIs

Storage & Evaluation

SQLite

persisted model artifacts / model registry

sequential simulation

sensitivity testing

Development & Testing

Git

GitHub

Pytest

Project Structure

app/
├── api/
│   ├── main.py
│   └── simulation.py
├── core/
├── features/
├── model/
├── monitoring/
├── simulation/
├── streamlit_app.py
└── ...

decisioning/
├── analyst_budget.py
├── cost_logic.py
├── decision_engine.py
├── strategies.py
├── suppression.py
└── thresholding.py

config/
data/
docs/
logs/
metrics/
models/
notebooks/
scripts/
tests/

Run Locally

Install dependencies

py -m pip install -r requirements.txt

Add PaySim data

data/raw/AIML Dataset.csv

Start FastAPI

If the local dashboard is configured for port 8002:

py -m uvicorn app.api.main:app --reload --port 8002

Start Streamlit

py -m streamlit run app/streamlit_app.py

The dashboard and API configuration must point to the same backend.

Testing

Relevant checks include:

model loading;

preprocessing;

threshold logic;

cost logic;

suppression;

decision-engine behaviour;

API responses;

invalid inputs;

sequential accounting; and

basic latency/performance behaviour.

Sensitivity analysis additionally tests robustness across different operating assumptions.

Research Limitations

This repository represents a research prototype, not a production fraud platform.

Important limitations include:

synthetic rather than institution-specific transaction data;

offline chronological replay rather than a live event stream;

retrospective fraud labels used for evaluation;

simplified analyst-capacity assumptions;

simulation-based cost estimates;

no continuous online retraining;

no production concept-drift response loop; and

no validation within a live financial institution.

Future Work

Potential extensions include:

evaluation on appropriately governed real transaction data;

live event-stream integration;

delayed analyst-feedback collection;

concept-drift detection;

controlled retraining and redeployment;

richer analyst-allocation models;

persistent production monitoring;

model and policy versioning; and

MLOps deployment pipelines.

Thesis Context

This repository was developed as part of a Master's thesis investigating how machine-learning fraud predictions can be transformed into operational decisions when investigation resources are limited.

The core contribution is the integration of:

fraud scoring → alert selection → suppression → prioritisation → analyst capacity → sequential evaluation → monitoring → sensitivity analysis

within one explainable decision-support framework.

The project therefore asks not only whether suspicious transactions can be detected, but whether machine-learning predictions can support better operational investigation decisions under realistic resource constraints.
