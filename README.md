# Decision-Centric Fraud Detection Framework

A research prototype for evaluating how machine-learning fraud scores can support operational fraud-investigation decisions under limited analyst capacity.

The system combines fraud-risk estimation with configurable alert-selection policies, transaction prioritisation, repeat-alert suppression, analyst-capacity constraints, sequential evaluation, monitoring, and sensitivity analysis.

## Live Demo

[Open the deployed Streamlit dashboard](https://decision-centric-fraud-framework-enwdwnh3oqxemezgpte6ug.streamlit.app/)

The deployed interface is provided as a research demonstration. It does not process live banking transactions and should not be interpreted as a production fraud-monitoring system.

---

## Project Scope

Conventional fraud-detection systems often focus on predictive performance alone. In practice, however, investigation resources are limited and not every suspicious transaction can be reviewed.

This project focuses on the operational decision that follows model scoring:

> **Which transactions should be investigated when available analyst capacity is constrained?**

The framework separates fraud prediction from fraud-response decision making.

The machine-learning model produces a fraud-risk score, while the decision layer determines:

- which transactions become candidate alerts;
- how alerts are prioritised;
- which repeated alerts are suppressed;
- which alerts can enter the analyst investigation queue;
- and how these decisions affect fraud detection and estimated operational cost.

The project compares two alert-selection approaches:

- **Static policy:** candidate alerts are generated using a fixed fraud-risk threshold.
- **Adaptive policy:** candidate eligibility, cost-aware ranking, and a configurable alert budget are combined to broaden or restrict the candidate pool relative to the Static baseline.

The main operational conclusions are based on **sequential chronological replay** rather than unrestricted batch evaluation.

---

## Dataset

The experiments use the **PaySim synthetic mobile-money dataset**.

**Dataset source:**  
[PaySim on Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1/data)

The implementation uses the following transaction variables:

| Variable | Description |
| --- | --- |
| `step` | Chronological PaySim step |
| `type` | Transaction type |
| `amount` | Transaction amount |
| `oldbalanceOrg` | Origin balance before the transaction |
| `newbalanceOrig` | Origin balance after the transaction |
| `oldbalanceDest` | Destination balance before the transaction |
| `newbalanceDest` | Destination balance after the transaction |
| `isFraud` | Ground-truth fraud label used for retrospective evaluation |

The identifiers displayed in the application are synthetic simulation identifiers. The system does not use real customer, card, account, or UPI identifiers.

The dataset is not included in the repository and is expected locally at:

```text
data/raw/AIML Dataset.csv
```

---

## Feature Engineering

The modelling pipeline includes the following engineered variables:

- `log_amount`
- `origin_balance_error`
- `destination_balance_error`
- `abs_origin_balance_error`
- `abs_destination_balance_error`

The dataset is split chronologically into training, validation, and test partitions to reduce temporal leakage.

---

## Machine-Learning Model

The fraud-scoring layer uses **Logistic Regression** within a scikit-learn preprocessing pipeline.

The preprocessing design includes:

- `StandardScaler` for numerical variables;
- `OneHotEncoder` for categorical variables;
- `ColumnTransformer` to combine preprocessing steps.

The model produces transaction-level fraud probabilities that are used by the downstream decision layer.

Probability calibration is part of the modelling workflow and is performed using validation-based **Platt scaling**.

The model is loaded from a persisted model artifact through the project configuration and model registry.

---

# Decision Layer

## Static Policy

The Static policy uses a fixed fraud-risk threshold.

Under the example dashboard configuration:

```text
Static threshold = 0.50
```

A transaction becomes a Static candidate alert when:

```text
Fraud risk ≥ 0.50
```

The threshold remains fixed throughout the evaluation.

Therefore, the number of Static alerts is determined by the fraud-score distribution of the evaluated transactions rather than by a predefined alert percentage.

---

## Adaptive Policy

The Adaptive policy separates three concepts that should not be confused:

1. **Static baseline alert volume**
2. **Adaptive Budget Multiplier**
3. **Minimum Adaptive risk floor**

### 1. Static baseline

The Static policy first establishes the baseline number of candidate alerts.

For example, under the current 10,000-transaction configuration:

```text
Static threshold = 0.50
        ↓
736 Static candidate alerts
```

### 2. Adaptive Budget Multiplier

The Budget Multiplier determines the maximum size of the Adaptive candidate-alert budget relative to the Static baseline.

For example:

```text
Static candidate alerts = 736
Budget Multiplier = 1.4×

736 × 1.4 = 1,030.4

Adaptive candidate budget = 1,030
```

Therefore:

```text
0.50 Static threshold
        ↓
736 Static alerts
        ↓
× 1.4 Budget Multiplier
        ↓
1,030 Adaptive candidate slots
```

The multiplier is applied to the **number of candidate alerts generated by the Static baseline**.

It is **not** applied to the Adaptive minimum risk threshold.

---

## Adaptive Eligibility and Selection

Once the Adaptive candidate budget has been established, the system determines which transactions are eligible to fill those candidate slots.

Under the current `risk_zone` configuration, the process can be represented as:

```text
Fraud risk ≥ 0.30
        ↓
Positive expected operational benefit
        ↓
Operational Rank Score
        ↓
Eligible transactions are ranked
        ↓
Highest-ranked transactions are selected
        ↓
Selection continues up to the Adaptive candidate budget
```

The **0.30 minimum risk floor** therefore determines eligibility.

The **1.4× Budget Multiplier** determines the maximum candidate budget.

These settings answer two different questions:

| Setting | Question |
| --- | --- |
| **Minimum risk floor (0.30)** | Which transactions are eligible to compete for Adaptive candidate slots? |
| **Budget Multiplier (1.4×)** | How many candidate slots may the Adaptive policy use? |

For example, a transaction with:

```text
Fraud risk = 0.43
```

would not satisfy the Static rule:

```text
0.43 < 0.50
```

but it can remain eligible under Adaptive because:

```text
0.43 ≥ 0.30
```

provided that it also satisfies the remaining Adaptive decision criteria and ranks highly enough to enter the available candidate budget.

Neither the minimum risk floor nor the Budget Multiplier changes the underlying machine-learning model.

---

## Fraud Risk and Rank Score

Fraud risk and Rank Score represent different quantities.

### Fraud Risk

**Fraud risk** is the probability produced by the machine-learning model.

Example:

```text
Fraud risk = 0.72
```

means that the model assigned a fraud probability of approximately 72%.

### Rank Score

**Rank Score** is an operational priority value used to order eligible candidate alerts.

Under the current `risk_zone` configuration, ranking incorporates fraud risk together with operational and cost-related information.

The Rank Score is used to answer:

> **If investigation resources are limited, which eligible alerts should be considered first?**

It is **not a probability** and should not be interpreted as a percentage.

---

# Repeat-Alert Suppression

The sequential evaluation includes repeat-alert suppression.

When multiple candidate alerts are associated with the same simulated entity within the configured suppression window, later alerts may be removed before analyst capacity is applied.

Suppression is intended to reduce repeated investigation workload.

It is not a separate fraud-classification model.

---

# Analyst Capacity

Analyst capacity represents the maximum number of alerts that may enter investigation during each operational step.

For example:

```text
Analyst capacity = 50 alerts per step
```

This constraint is separate from the Adaptive candidate budget.

An Adaptive policy may therefore generate hundreds of candidate alerts while only the highest-priority subset can actually be investigated.

Each candidate ends in one of three operational outcomes:

| Outcome | Meaning |
| --- | --- |
| **Investigated** | Alert entered the analyst investigation queue |
| **Suppressed** | Alert was removed by repeat-alert suppression |
| **Capacity rejected** | Alert remained eligible but available analyst capacity was exhausted |

The backend validates:

```text
Candidate alerts
=
Investigated alerts
+
Suppressed alerts
+
Capacity-rejected alerts
```

Unused analyst capacity is not carried forward to later operational steps.

---

# Sequential Evaluation

The main operational evaluation is an **offline chronological replay**.

Transactions are processed according to the PaySim `step` variable.

Transactions sharing the same step are treated as one operational decision cycle.

Within each step, the system performs:

1. Fraud-risk scoring
2. Candidate-alert generation
3. Repeat-alert suppression
4. Priority ranking
5. Analyst-capacity enforcement
6. Investigation-queue selection
7. Retrospective comparison with PaySim fraud labels

The sequential evaluation is **not a live event-processing system**.

The correct description of the implementation is:

> **Offline sequential simulation / chronological replay**

Batch evaluation is retained as an ideal methodological reference before sequential operational constraints are applied.

---

# Operational Step Explorer

The Sequential Workflow includes an interactive **Operational Step Explorer**.

Instead of displaying only aggregate results, the explorer allows the user to inspect what happened during individual chronological PaySim steps.

The user can select an operational step and switch between:

```text
Static
Adaptive
```

For each step, the dashboard reports:

- Transactions processed
- Candidate alerts
- Candidate-alert rate
- Eligible alerts after suppression
- Investigated alerts
- Analyst capacity
- Capacity-rejected alerts
- Frauds present
- Frauds detected
- Fraud recall within the selected step

This makes the sequential component explicitly temporal:

```text
How the decision system works
        ↓
What happened in Step 1
        ↓
What happened in Step 2
        ↓
...
        ↓
What happened in Step 7
```

---

## Interactive Adaptive Budget Analysis

When the **Adaptive policy** is selected, the Operational Step Explorer also allows the Budget Multiplier to be changed interactively.

For example:

```text
1.0×
1.1×
1.2×
1.3×
1.4×
1.5×
```

Changing the multiplier recalculates the Adaptive scenario while leaving the main dashboard configuration unchanged.

The explorer then exposes the numerical decision path behind the resulting candidate alerts.

This includes:

### Risk-zone composition

The dashboard separates selected Adaptive candidates into:

```text
Fraud risk ≥ 0.50
```

and:

```text
Fraud risk 0.30–0.50
```

The second group represents candidate transactions that would fail the Static 0.50 threshold but remain eligible under the Adaptive policy.

The explorer also reports:

- Lowest selected fraud risk
- Median selected fraud risk
- Highest selected fraud risk

### Ranking

For selected Adaptive candidates, the explorer reports:

- Highest selected Rank Score
- Median selected Rank Score
- Lowest selected Rank Score

This makes the prioritisation stage visible rather than treating Adaptive selection as another simple threshold.

---

## Global Multiplier vs Step-Local Effect

An important distinction is made between the **configured global Budget Multiplier** and its **observed effect within an individual operational step**.

For example:

```text
Configured Budget Multiplier = 1.4×
```

does not mean:

```text
Adaptive alerts in Step 1
=
Static alerts in Step 1 × 1.4
```

The multiplier determines the **global Adaptive candidate budget**.

Eligible transactions are ranked across the evaluation, and the selected transactions are subsequently observed within their chronological PaySim steps.

Therefore, an individual step may show, for example:

```text
Static candidates = 294
Adaptive candidates = 359

359 / 294 = 1.22×
```

even though:

```text
Configured global multiplier = 1.4×
```

The **1.4×** is the configured global policy setting.

The **1.22×** is the observed local expansion within that particular step.

These are intentionally different quantities.

---

# Operational Cost

The project uses a simulation-based estimate of operational cost for comparing policies under identical assumptions.

The current formulation is:

```text
Estimated operational cost
=
Investigation cost
+
Estimated missed-fraud value
```

Investigation cost is calculated as:

```text
Investigated alerts
×
Assumed investigation cost per alert
```

Missed-fraud value is derived from transaction amounts associated with fraud cases that were not detected, together with the configured false-negative cost factor.

These values are experimental decision-support measures.

They are **not observed banking losses or accounting figures**.

---

# Dashboard

The Streamlit application is organised into five main analytical sections.

## 1. Executive Summary

The Executive Summary presents the primary Static-versus-Adaptive comparison.

It reports:

- Investigated alerts
- Frauds detected
- Frauds missed
- Precision
- Recall
- Estimated operational cost
- Cost difference
- Policy interpretation

A **Quick Guide** provides a short introduction for first-time users and directs them to the relevant dashboard sections.

Sequential results are treated as the primary operational evidence.

---

## 2. Analyst Capacity

The Analyst Capacity section answers:

> **Which alerts were investigated or excluded, and why?**

It includes:

- Fraud Investigation Funnel
- Candidate alerts
- Investigated alerts
- Suppressed alerts
- Capacity-rejected alerts
- Analyst capacity by operational step
- Fraud risk by transaction type
- Prioritised Investigation Queue
- Transaction-level decision explanations

The investigation queue includes both investigated and non-investigated candidate alerts so that the operational cut-off can be inspected directly.

---

## 3. Sequential Workflow

The Sequential Workflow answers:

> **How did the decision process evolve over time?**

It includes:

- Seven-step decision process
- Interactive Operational Step Explorer
- Static/Adaptive policy selector
- Interactive Adaptive Budget Multiplier
- Step-level candidate and investigation metrics
- Candidate priority breakdown
- Expandable numerical explanations
- Batch-versus-Sequential methodological comparison
- Clarification of offline replay versus real-time processing

This gives the Sequential Workflow a different purpose from the Analyst Capacity section:

```text
Analyst Capacity
→ Which alerts were selected or excluded overall?

Sequential Workflow
→ How did those decisions evolve step by step?
```

---

## 4. Monitoring

The Monitoring section divides the replay into consecutive reporting windows.

Monitoring windows are used for reporting and trend inspection.

They are separate from operational steps and do not control analyst-capacity resets.

The monitoring view reports:

- Candidate alerts
- Investigated alerts
- Capacity overflow
- Missed frauds
- Recall
- Estimated operational cost

This represents **operational monitoring of the offline replay**.

It is not an MLOps monitoring pipeline.

---

## 5. Sensitivity Analysis

Sensitivity analysis evaluates how the decision layer behaves when one operating parameter changes while the remaining settings are held constant.

The current experiments include:

| Parameter | Tested configuration |
| --- | --- |
| Transaction volume | Multiple evaluation sizes |
| Analyst capacity | Multiple alerts-per-step settings |
| Investigation cost | Multiple assumed cost values |
| Suppression window | Multiple step-based settings |
| Adaptive Budget Multiplier | Multiple multiplier settings |
| Static threshold | Multiple fraud-risk thresholds |
| Minimum Adaptive threshold | Multiple minimum fraud-risk thresholds |

The experiments follow a **one-parameter-at-a-time** design.

The Sensitivity Analysis allows the user to distinguish cases in which:

- Adaptive is preferable
- Static is preferable
- The two policies produce effectively equivalent outcomes

Preference is evaluated using fraud recall and estimated operational cost under the tested assumptions.

---

# Current Example Configuration

For the current 10,000-transaction sequential scenario with analyst capacity set to 50 alerts per operational step:

| Metric | Static | Adaptive |
| --- | ---: | ---: |
| Investigated alerts | 313 | 349 |
| Frauds detected | 27 | 30 |
| Frauds missed | 41 | 38 |
| Precision | 8.6% | 8.6% |
| Recall | 39.7% | 44.1% |
| Estimated operational cost | €1,745,391.01 | €1,726,843.29 |

Under this configuration, the Adaptive policy produces:

```text
Recall:
39.7% → 44.1%

Estimated operational cost:
€1.745M → €1.727M
```

The results demonstrate the operational trade-off produced by the decision layer under the selected simulation assumptions.

These values are based on synthetic PaySim data and should **not** be generalised to real banking environments.

---

# Example Capacity Scenario

The Decision Scenario Explorer can also be used to examine the effect of analyst capacity.

For example, increasing Adaptive capacity from **50 to 60 alerts per operational step** produced:

| Outcome | 50 per step | 60 per step |
| --- | ---: | ---: |
| Candidate alerts | 1,020 | 1,020 |
| Investigated alerts | 349 | 402 |
| Frauds detected | 30 | 32 |
| Recall | 44.1% | 47.1% |
| Suppressed alerts | 21 | 26 |
| Capacity-rejected alerts | 650 | 592 |

This illustrates an important distinction:

> Increasing analyst capacity does not necessarily generate more candidate alerts. It determines how many existing candidates can actually enter investigation.

---

# Technology Stack

| Area | Technology |
| --- | --- |
| Programming language | Python |
| Data processing | Pandas, NumPy |
| Machine learning | scikit-learn |
| API | FastAPI |
| Dashboard | Streamlit |
| Visualisation | Matplotlib, Streamlit charts |
| Model persistence | Joblib / persisted model artifacts |
| Version control | Git, GitHub |

---

# Application Structure

The project is organised around separate modelling, API, decision, simulation, and dashboard components.

```text
app/
├── api/
├── core/
├── features/
├── model/
├── monitoring/
├── simulation/
└── streamlit_app.py

decisioning/
├── analyst_budget.py
├── cost_logic.py
├── decision_engine.py
├── strategies.py
├── suppression.py
└── thresholding.py

config/
data/
models/
scripts/
tests/
```

---

# API

The Streamlit dashboard obtains simulation results from the FastAPI backend.

The dashboard uses API functionality for:

- Sequential policy evaluation
- Static-versus-Adaptive comparison
- Transaction-level decision outputs
- Operational-step outputs
- Sensitivity analysis
- Alternative Adaptive Budget Multiplier scenarios

The API base URL is configured through the `API_BASE_URL` environment variable.

When no environment variable is provided, local development uses:

```text
http://127.0.0.1:8002
```

---

# Running Locally

## 1. Create and Activate a Virtual Environment

### Windows

```bash
py -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Add the PaySim Dataset

Place the dataset at:

```text
data/raw/AIML Dataset.csv
```

## 4. Start the FastAPI Backend

```bash
py -m uvicorn app.api.main:app --reload --port 8002
```

## 5. Start the Streamlit Application

```bash
py -m streamlit run app/streamlit_app.py
```

The Streamlit application and FastAPI backend must use the same API configuration.

---

# Deployment

The Streamlit interface is publicly deployed as a research demonstration.

Deployment makes the dashboard accessible through a browser but does not change the underlying evaluation method.

The application still uses:

- synthetic PaySim data;
- stored transactions;
- offline chronological replay;
- simulated analyst capacity;
- retrospective fraud labels.

Deployment should therefore not be interpreted as evidence of:

- production banking integration;
- live payment validation;
- live fraud operations;
- or real-time transaction streaming.

---

# Testing

The repository includes an automated `pytest` test suite covering the main decision-support, sequential-processing, API, and dashboard-logic components of the prototype.

The regression suite contains **88 automated tests**.

Testing covers:

- Static and Adaptive decision logic
- Score-, benefit-, hybrid-, and risk-zone ranking
- Expected fraud-loss calculations
- Investigation-cost calculations
- Expected-benefit calculations
- Risk-zone constraints
- Alert-budget constraints
- Invalid-parameter handling
- Analyst-capacity enforcement
- Prioritised investigation-queue ordering
- Chronological sequential processing
- Repeat-alert suppression
- Capacity-rejected alerts
- Sequential accounting consistency
- Operating-curve behaviour
- Budget Multiplier behaviour
- REST API responses
- Sequential API scenarios
- Dashboard monitoring transformations
- Dashboard trend-classification logic

The complete test suite can be executed with:

```bash
py -m pytest app/tests -q
```

Latest full regression run:

```text
88 passed
```

These tests verify implementation consistency within the research prototype.

They do not constitute evidence of production readiness or external validity on real banking data.

---

# Limitations

## Synthetic Data

The evaluation uses PaySim rather than institution-specific banking data.

The results demonstrate behaviour within the experimental framework and do not establish external validity on real financial transactions.

## Offline Replay

The Sequential Workflow uses stored transactions processed in chronological order.

It does not receive continuously arriving payment events.

## Simplified Analyst Capacity

Analyst capacity is represented as a fixed number of alerts per operational step.

Real investigation capacity would also depend on staffing, case complexity, working hours, investigation duration, and organisational processes.

## Retrospective Labels

Ground-truth fraud labels are available for evaluation after the simulated decision has been made.

In a production environment, confirmed fraud outcomes would usually arrive with delay.

## Experimental Cost Assumptions

Investigation cost and missed-fraud value are simulation assumptions.

They are used to compare decision policies under identical conditions and should not be interpreted as observed financial losses.

## Synthetic Identity and Suppression Logic

Repeat-alert suppression operates on simulated identifiers available within the research framework.

The implementation should not be interpreted as modelling a real institution's customer-resolution or case-management process.

---

# Future Work

Potential extensions include:

- Evaluation with appropriately governed real transaction data
- Integration with a live transaction stream
- Explicit mapping between PaySim steps and real operational time
- Delayed analyst-feedback integration
- Monitoring for changes in transaction and fraud patterns
- More realistic analyst-capacity models
- Richer false-positive and missed-fraud cost models
- Comparison of additional alert-ranking strategies
- Dynamic budget allocation across operational periods
- Evaluation of alternative adaptive thresholding strategies
- Integration with case-management workflows

---

# Research Context

This repository was developed as part of a **Master's thesis** investigating how fraud-risk predictions can support operational decisions when investigation resources are limited.

The main contribution is not the fraud classifier alone.

Instead, the project evaluates how machine-learning predictions can be translated into operational investigation decisions through a configurable decision layer supporting:

- alert selection;
- cost-aware prioritisation;
- repeat-alert suppression;
- analyst-capacity constraints;
- chronological sequential evaluation;
- operational monitoring;
- sensitivity analysis;
- and transaction-level decision explanations.

The framework is intended as a **decision-support research prototype**, not as a production fraud platform.
