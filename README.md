# Decision-Centric Fraud Detection Framework

**MSc Dissertation — Fraud Detection Decision Support under Limited Analyst Capacity**

A research prototype that converts machine-learning fraud probabilities into **prioritised investigation decisions** under limited analyst capacity.

[Live Streamlit Demo](https://decision-centric-fraud-framework-enwdwnh3oqxemezgpte6ug.streamlit.app/)

> **Scope:** Synthetic PaySim data · offline chronological replay · simulation-based operational costs · not a production or live banking system.

---

## 1. System Architecture

```text
PaySim Transactions
        ↓
Feature Engineering
        ↓
Logistic Regression + Probability Calibration
        ↓
Fraud Risk (`fraud_score`)
        ↓
Static / Adaptive Alert Selection
        ↓
Repeat-Alert Suppression
        ↓
Rank Score Prioritisation
        ↓
Analyst Capacity per Operational Step
        ↓
Investigated / Suppressed / Capacity-Rejected
        ↓
Recall · Precision · Operational Cost
```

| Layer | Role |
| --- | --- |
| **ML Layer** | Estimates transaction-level Fraud Risk |
| **Decision Layer** | Converts Fraud Risk into alerts and operational priority |
| **Sequential Simulation** | Applies suppression and analyst capacity chronologically |
| **Evaluation Layer** | Measures fraud detection and estimated operational cost |
| **Dashboard** | Exposes results, queues, explanations and experiments |

---

## 2. Dataset and Feature Representation

The project uses the **PaySim synthetic mobile-money dataset**.

### Original PaySim Columns

| Column | Representation |
| --- | --- |
| `step` | Chronological PaySim period |
| `type` | Transaction type |
| `amount` | Transaction value |
| `oldbalanceOrg` | Origin balance before the transaction |
| `newbalanceOrig` | Origin balance after the transaction |
| `oldbalanceDest` | Destination balance before the transaction |
| `newbalanceDest` | Destination balance after the transaction |
| `isFraud` | Ground-truth target used for training and retrospective evaluation |

### Engineered Features

| Feature | Representation |
| --- | --- |
| `log_amount` | Log-scaled transaction amount |
| `origin_balance_error` | Origin-side balance inconsistency |
| `destination_balance_error` | Destination-side balance inconsistency |
| `abs_origin_balance_error` | Absolute origin-side inconsistency |
| `abs_destination_balance_error` | Absolute destination-side inconsistency |

### Model Input Representation

```text
7 original transaction fields
+
5 engineered features
=
12 model inputs
```

The model inputs consist of:

```text
11 numerical features
+
1 categorical feature (`type`)
```

> `isFraud` is the target/evaluation label. It is **not supplied to the model as a predictive input**.

---

## 3. Machine-Learning Pipeline

```text
Original Transaction Fields
        ↓
Engineered Features
        ↓
ColumnTransformer
   ├── StandardScaler → Numerical Features
   └── OneHotEncoder  → Transaction Type
        ↓
Logistic Regression
        ↓
Probability Calibration
        ↓
Fraud Risk (`fraud_score`)
```

The dataset is divided chronologically into:

```text
Training
→ Validation
→ Test
```

### Fraud Risk

`fraud_score` represents the model-estimated probability of fraud.

Example:

```text
fraud_score = 0.42
→ estimated Fraud Risk = 42%
```

> **Fraud Risk is a model probability. It is not an alert decision and it is not a Rank Score.**

---

## 4. Decision Policies

### 4.1 Static Policy

The Static policy uses a fixed Fraud Risk threshold.

```text
Static Threshold = 0.50
```

Decision rule:

```text
Fraud Risk ≥ 0.50
→ Static Candidate Alert
```

For the current 10,000-transaction evaluation:

```text
Static Candidate Alerts = 736
```

---

### 4.2 Adaptive Policy — Eligibility

The Adaptive policy separates:

1. **Eligibility**
2. **Operational Priority**
3. **Alert Budget**

Current eligibility rule:

```text
Fraud Risk ≥ 0.30
AND
Expected Benefit > 0
```

The `0.30` value is the Adaptive **minimum risk floor**.

It determines which transactions are eligible to compete for the Adaptive alert budget.

---

### 4.3 Adaptive Policy — Operational Priority

For each eligible transaction:

```text
Expected Fraud Loss
=
Fraud Risk × Amount × False-Negative Factor
```

```text
Expected Investigation Cost
=
(1 − Fraud Risk) × Investigation Cost
```

Then:

```text
Expected Benefit
=
Expected Fraud Loss − Expected Investigation Cost
```

Under the current `risk_zone` policy:

```text
Rank Score = Expected Benefit
```

Eligible alerts are ordered from **highest to lowest Rank Score**.

> **Fraud Risk = estimated fraud probability.**  
> **Rank Score = operational investigation priority.**

There is no fixed rule such as:

```text
Rank Score ≥ 25
```

Instead, the effective cut-off emerges dynamically from the ordered alerts and the available Adaptive alert budget.

---

### 4.4 Adaptive Policy — Budget Multiplier

The Budget Multiplier determines the maximum Adaptive alert budget relative to the Static candidate-alert volume.

Example with `1.4×`:

```text
Static Candidate Alerts = 736
Budget Multiplier       = 1.4×

736 × 1.4
=
1,030.4

Adaptive Alert Budget
=
1,030 alerts
```

The Budget Multiplier does **not** modify:

- Fraud Risk
- Transaction Amount
- Rank Score
- Analyst Capacity

It determines how many of the highest-ranked eligible Adaptive alerts may be retained.

### Adaptive Decision Flow

```text
Fraud Risk ≥ 0.30
        ↓
Expected Benefit > 0
        ↓
Rank Score Calculated
        ↓
Eligible Alerts Ordered by Rank Score
        ↓
Budget Multiplier Determines Alert Budget
        ↓
Highest-Ranked Alerts Retained
```

---

## 5. Sequential Operational Logic

The main operational evaluation uses an **offline sequential simulation / chronological replay**.

Transactions are processed according to PaySim `step`.

Transactions sharing the same `step` belong to the same operational decision cycle.

### Seven-Step Decision Process

| Step | Input | Processing | Output |
| ---: | --- | --- | --- |
| **1** | Original PaySim fields | Transactions are replayed chronologically | Transaction ready for feature processing |
| **2** | Original + engineered features | ML pipeline estimates Fraud Risk | `fraud_score` |
| **3** | Fraud Risk + policy parameters | Static or Adaptive rules create candidate alerts | Candidate alerts |
| **4** | Candidate alerts + simulated entity history | Repeated alerts may be suppressed | Eligible alerts |
| **5** | Eligible alerts + Rank Score | Alerts are ordered by operational priority | Prioritised alerts |
| **6** | Prioritised alerts + analyst capacity | Per-step capacity is applied | Investigated / Capacity-Rejected |
| **7** | Decisions + `isFraud` | Decisions are evaluated retrospectively | Recall / Precision / Cost |

### Repeat-Alert Suppression

Repeated candidate alerts associated with the same simulated entity may be suppressed within the configured suppression window.

```text
Candidate Alert
        ↓
Repeat-Alert Check
   ├── Repeated → Suppressed
   └── Not Repeated → Continue
```

Suppression is an **operational rule**, not a fraud-classification model.

### Analyst Capacity

Example:

```text
Analyst Capacity
=
50 investigations per operational step
```

Capacity is applied independently inside every operational step.

Unused capacity is **not carried forward**.

Sequential ranking follows:

```text
1. rank_score      → descending
2. fraud_score     → descending
3. transaction_id  → ascending
```

Candidate-alert accounting:

```text
Candidate Alerts
=
Investigated
+
Suppressed
+
Capacity-Rejected
```

---

# 6. Dashboard Structure

The Streamlit dashboard follows the current analytical sequence:

```text
1. Executive Summary
        ↓
2. Sequential Workflow
        ↓
3. Analyst Capacity
        ↓
4. Monitoring
        ↓
5. Sensitivity Analysis
```

---

## Slide 1 — Executive Summary

**Purpose:** present the main Static-versus-Adaptive operational result.

| Component | Representation |
| --- | --- |
| Recommended Policy | Current preferred decision policy |
| Investigated Alerts | Alerts entering analyst investigation |
| Frauds Detected | Fraudulent transactions successfully investigated |
| Frauds Missed | Fraudulent transactions not investigated |
| Precision | Fraud concentration among investigated alerts |
| Recall | Share of total frauds detected |
| Operational Cost | Simulation-based estimated policy cost |

The **Sequential replay** is treated as the main operational evidence.

Batch evaluation is retained only as an ideal methodological reference.

---

## Slide 2 — Sequential Workflow

**Purpose:** show how operational decisions evolve chronologically.

### Structure

```text
Seven-Step Decision Process
        ↓
Model Input Explanation
        ↓
Static / Adaptive Policy Selection
        ↓
Adaptive Budget Multiplier
        ↓
Operational Step Explorer
        ↓
Step-Level Alert Representation
        ↓
Eligibility + Rank Score Explanation
        ↓
Batch vs Sequential Reference
        ↓
Offline Replay Clarification
```

### Operational Step Explorer

For each selected PaySim step:

| Metric | Meaning |
| --- | --- |
| **Transactions Processed** | Transactions present in the selected step |
| **Candidate Alerts** | Alerts generated by the selected policy |
| **Suppressed** | Repeated alerts removed before capacity allocation |
| **Investigated** | Alerts accepted within analyst capacity |
| **Capacity-Rejected** | Eligible alerts excluded because capacity was exhausted |
| **Frauds Detected** | Fraudulent transactions among investigated alerts |

### Step-Level Alert Representation

The explorer exposes alert-level information such as:

```text
Transaction ID
Step
Transaction Type
Amount
Fraud Risk
Rank Score
Priority
Suppression Status
Investigation Status
Final Sequential Decision
```

This allows the user to inspect how a transaction moves from model prediction to operational outcome.

---

## Slide 3 — Analyst Capacity

**Purpose:** show which candidate alerts were investigated or excluded and why.

### Structure

```text
Fraud Investigation Funnel
        ↓
Candidate-Alert Accounting
        ↓
Analyst Capacity by Operational Step
        ↓
Fraud Risk by Transaction Type
        ↓
Prioritised Investigation Queue
        ↓
Alert Decision Explanation
```

### Final Alert Outcomes

| Outcome | Meaning |
| --- | --- |
| **Investigated** | Alert entered analyst investigation |
| **Suppressed** | Alert removed by repeat-alert suppression |
| **Capacity-Rejected** | Alert remained eligible but analyst capacity was exhausted |

### Investigation Funnel

```text
Transactions
        ↓
Candidate Alerts
        ↓
Suppression
        ↓
Prioritised Alerts
        ↓
Analyst Capacity
        ↓
Investigated Alerts
```

The Prioritised Investigation Queue contains both investigated and non-investigated candidates so the operational cut-off remains inspectable.

---

## Slide 4 — Monitoring

**Purpose:** inspect how operational results change across the chronological replay.

| Metric | Representation |
| --- | --- |
| Candidate Alerts | Policy-generated workload |
| Investigated Alerts | Analyst workload |
| Capacity Overflow | Alerts rejected because capacity was exhausted |
| Frauds Missed | Fraudulent cases not investigated |
| Recall | Fraud coverage |
| Estimated Operational Cost | Simulation-based policy cost |

Monitoring windows are **reporting units**.

They are not PaySim operational steps and they do not control analyst-capacity resets.

> Monitoring represents operational analysis of the offline replay, not a production MLOps monitoring pipeline.

---

## Slide 5 — Sensitivity Analysis

**Purpose:** test how operational results change when one parameter changes while the others remain fixed.

### Parameters Tested

| Parameter | Values / Range |
| --- | --- |
| Transaction Volume | `1,000` · `3,000` · `10,000` |
| Analyst Capacity | `10–100` alerts per step |
| Investigation Cost | `€5` · `€10` · `€15` · `€20` · `€25` |
| Suppression Window | `0` · `1` · `2` · `3` · `5` steps |
| Adaptive Budget Multiplier | `1.0–2.0` |
| Static Threshold | `0.30` · `0.40` · `0.50` · `0.60` · `0.70` |
| Minimum Adaptive Threshold | `0.10` · `0.20` · `0.30` · `0.40` · `0.50` |

### Sensitivity Workflow

```text
Decision Scenario Explorer
        ↓
Baseline Configuration
        ↓
Static vs Adaptive Comparison
        ↓
Experiment Drill-Down
        ↓
Recall Comparison
        ↓
Estimated Cost Comparison
        ↓
Policy Interpretation
```

The analysis uses a **one-parameter-at-a-time** design.

---

# 7. Current Baseline Results

### Configuration

```text
Transactions Evaluated = 10,000
Analyst Capacity       = 50 alerts / operational step
Static Threshold       = 0.50
Adaptive Risk Floor    = 0.30
```

### Static vs Adaptive

| Metric | Static | Adaptive | Δ Adaptive vs Static |
| --- | ---: | ---: | ---: |
| **Investigated Alerts** | 313 | 349 | +36 |
| **Frauds Detected** | 27 | 30 | +3 |
| **Frauds Missed** | 41 | 38 | −3 |
| **Precision** | 8.6% | 8.6% | ≈ 0 pp |
| **Recall** | 39.7% | 44.1% | **+4.4 pp** |
| **Estimated Operational Cost** | €1,745,391.01 | €1,726,843.29 | **−€18,547.72** |

### Baseline Effect

```text
Recall
39.7% → 44.1%

Frauds Detected
27 → 30

Frauds Missed
41 → 38

Estimated Operational Cost
€1.745M → €1.727M
```

Under the current configuration, Adaptive:

```text
+3 detected frauds
+4.4 percentage points recall
−3 missed frauds
≈ €18.5K lower estimated operational cost
```

> These are simulation-based results using synthetic PaySim data, not observed banking outcomes.

---

## 8. Example Capacity Scenario

Increasing Adaptive analyst capacity:

```text
50 → 60 alerts per operational step
```

produces:

| Outcome | Capacity 50 | Capacity 60 | Change |
| --- | ---: | ---: | ---: |
| Candidate Alerts | 1,020 | 1,020 | 0 |
| Investigated Alerts | 349 | 402 | +53 |
| Frauds Detected | 30 | 32 | +2 |
| Recall | 44.1% | 47.1% | +3.0 pp |
| Suppressed Alerts | 21 | 26 | +5 |
| Capacity-Rejected Alerts | 650 | 592 | −58 |

This illustrates the separation between:

```text
Candidate Generation
≠
Analyst Capacity
```

Candidate volume remains unchanged while investigation coverage increases.

---

## 9. Operational Cost Representation

```text
Estimated Operational Cost
=
Investigation Cost
+
Estimated Missed-Fraud Value
```

Investigation component:

```text
Investigation Cost
=
Investigated Alerts
×
Assumed Cost per Investigation
```

The cost values are **experimental policy-comparison measures**.

They are not observed financial losses.

---

## 10. Technology Stack

| Area | Technology |
| --- | --- |
| Programming Language | Python |
| Data Processing | Pandas, NumPy |
| Machine Learning | scikit-learn |
| API | FastAPI |
| Dashboard | Streamlit |
| Visualisation | Matplotlib, Streamlit |
| Testing | pytest |
| Version Control | Git, GitHub |

---

## 11. Repository Structure

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

## 12. API Role

The FastAPI backend connects the ML and decision layers with the Streamlit interface.

It supports:

- policy comparison
- sequential simulation
- transaction-level decision outputs
- operational-step results
- Budget Multiplier scenarios
- sensitivity analysis

---

## 13. Testing

Current automated regression suite:

```text
88 tests passed
```

| Test Area | Tests | Result |
| --- | ---: | --- |
| Decision Logic | 16 | 16 passed |
| Analyst Queue and Capacity | 10 | 10 passed |
| Sequential Simulation | 12 | 12 passed |
| Operating-Curve Logic | 19 | 19 passed |
| REST API | 14 | 14 passed |
| Dashboard Logic | 17 | 17 passed |
| **Total** | **88** | **88 passed** |

Key checks include:

- Static and Adaptive decision logic
- Rank Score calculations
- Expected Benefit calculations
- risk-zone constraints
- Budget Multiplier behaviour
- chronological processing
- repeat-alert suppression
- analyst-capacity enforcement
- candidate-alert accounting
- API outputs
- dashboard transformations

---

## 14. Run Locally

### Create Environment

```bash
py -m venv .venv
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dataset

Place PaySim at:

```text
data/raw/AIML Dataset.csv
```

### Start FastAPI

```bash
py -m uvicorn app.api.main:app --reload --port 8002
```

### Start Streamlit

```bash
py -m streamlit run app/streamlit_app.py
```

Default local API:

```text
http://127.0.0.1:8002
```

---

## 15. Limitations

- Synthetic PaySim transactions
- Offline chronological replay rather than live streaming
- Fixed per-step analyst-capacity abstraction
- Simulation-based cost assumptions
- Retrospective `isFraud` labels for evaluation
- Synthetic entity identities for suppression logic

---

## 16. Core Research Contribution

```text
Transaction Columns
        ↓
Engineered Features
        ↓
Fraud Risk
        ↓
Alert Eligibility
        ↓
Rank Score
        ↓
Adaptive Alert Budget
        ↓
Repeat-Alert Suppression
        ↓
Analyst Capacity
        ↓
Investigation
        ↓
Operational Outcome
```

The central contribution is the **decision layer that translates ML fraud scores into explainable, prioritised and capacity-constrained investigation decisions**, rather than the fraud classifier alone.
