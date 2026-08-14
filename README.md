Decision-Centric Fraud Detection Framework

A research prototype for evaluating how machine-learning fraud scores can support operational fraud-investigation decisions under limited analyst capacity.

The system combines fraud-risk estimation with configurable alert-selection policies, transaction prioritisation, repeat-alert suppression, analyst-capacity constraints, sequential evaluation, monitoring, and sensitivity analysis.

Live Demo

The current Streamlit deployment is available at:

Open the deployed Streamlit dashboard

The deployed interface is provided as a research demonstration. It does not process live banking transactions and should not be interpreted as a production fraud-monitoring system.

Project Scope

Conventional fraud-detection systems often focus on predictive performance alone. In practice, however, investigation resources are limited and not every suspicious transaction can be reviewed.

This project focuses on the operational decision that follows model scoring:

Which transactions should be investigated when available analyst capacity is constrained?

The framework separates fraud prediction from fraud-response decision making. The machine-learning model produces a fraud-risk score, while the decision layer determines which transactions become candidate alerts, how they are prioritised, which repeated alerts are suppressed, and which alerts can enter the analyst queue.

The project compares two alert-selection approaches:

a Static policy based on a fixed fraud-risk threshold;

an Adaptive policy based on a minimum fraud threshold and a configurable candidate-alert budget.

The main operational conclusions are based on sequential chronological replay rather than unrestricted batch evaluation.

Dataset

The experiments use the PaySim synthetic mobile-money dataset.

The implementation uses the following transaction variables:

Variable

Description

step

Chronological PaySim step

type

Transaction type

amount

Transaction amount

oldbalanceOrg

Origin balance before the transaction

newbalanceOrig

Origin balance after the transaction

oldbalanceDest

Destination balance before the transaction

newbalanceDest

Destination balance after the transaction

isFraud

Ground-truth fraud label used for retrospective evaluation

The identifiers displayed in the application are synthetic simulation identifiers. The system does not use real customer, card, account, or UPI identifiers.

The dataset is not included in the repository and is expected locally at:

data/raw/AIML Dataset.csv

Feature Engineering

The modelling pipeline includes the following engineered variables:

log_amount

origin_balance_error

destination_balance_error

abs_origin_balance_error

abs_destination_balance_error

The dataset is split chronologically into training, validation, and test partitions to reduce temporal leakage.

Machine-Learning Model

The fraud-scoring layer uses Logistic Regression within a scikit-learn preprocessing pipeline.

The preprocessing design includes:

StandardScaler for numerical variables;

OneHotEncoder for categorical variables;

ColumnTransformer to combine preprocessing steps.

The model produces transaction-level fraud probabilities that are used by the downstream decision layer.

Probability calibration is part of the modelling workflow and is performed using validation-based Platt scaling.

The model is loaded from a persisted model artifact through the project configuration and model registry. The application therefore does not depend on in-memory training history when it starts.

Decision Layer

Static Policy

The Static policy uses a fixed fraud-risk threshold.

A transaction becomes a candidate alert when its fraud score reaches the configured threshold.

The threshold is constant throughout the replay.

Adaptive Policy

The Adaptive policy uses two main controls:

a minimum Adaptive fraud threshold;

an Adaptive budget multiplier.

The minimum threshold determines the lowest fraud score that can enter the Adaptive candidate set.

The budget multiplier controls the maximum size of the Adaptive candidate-alert budget relative to the Static baseline alert volume.

The Adaptive policy therefore changes candidate selection without changing the underlying machine-learning model.

Fraud Risk and Rank Score

Fraud risk and rank score represent different quantities.

Fraud risk is the probability assigned by the machine-learning model.

Rank score is an operational priority value used to order eligible alerts before analyst capacity is applied.

Under the current risk_zone ranking configuration, the ranking logic incorporates fraud risk, transaction amount, investigation-cost assumptions, and a false-negative cost factor.

The rank score is not a probability and should not be interpreted as a percentage.

Repeat-Alert Suppression

The sequential evaluation includes repeat-alert suppression.

When multiple alerts are associated with the same simulated entity within the configured suppression window, later alerts may be removed before analyst capacity is applied.

Suppression is used to reduce repeated investigation workload. It is not a separate fraud-classification model.

Analyst Capacity

Analyst capacity is represented as the maximum number of alerts that may enter investigation during each operational step.

Capacity is applied independently within each step.

Unused capacity is not carried forward to later steps.

Each policy candidate therefore ends in one of the following operational outcomes:

Outcome

Meaning

Investigated

The alert entered the analyst queue

Suppressed

The alert was removed by repeat-alert suppression

Capacity rejected

The alert remained eligible but could not be investigated because the step capacity was exhausted

The backend validates the following accounting relationship:

Candidate alerts
=
Investigated alerts
+
Suppressed alerts
+
Capacity-rejected alerts

Sequential Evaluation

The main operational evaluation is an offline chronological replay.

Transactions are processed according to the PaySim step variable. Transactions sharing the same step are treated as one operational decision cycle.

Within each step, the system performs the following operations:

fraud-risk scoring;

candidate-alert generation;

repeat-alert suppression;

priority ranking;

analyst-capacity enforcement;

investigation-queue selection;

retrospective comparison with PaySim fraud labels.

The sequential evaluation is not a live event-processing system.

A correct description of the current implementation is:

offline sequential simulation / chronological replay

Batch evaluation is retained only as an ideal methodological reference before sequential operational constraints are applied.

Operational Cost

The project uses a simulation-based estimate of operational cost for comparing policies under identical assumptions.

The current formulation combines investigation cost with the estimated value of missed fraud:

Estimated operational cost
=
Investigation cost
+
Estimated missed-fraud value

Investigation cost is calculated as:

Investigated alerts × assumed investigation cost per alert

Missed-fraud value is derived from transaction amounts associated with fraud cases that were not detected, together with the configured false-negative cost factor.

These values are experimental decision-support measures. They are not observed banking losses or accounting figures.

Dashboard

The Streamlit application is organised into five main analytical sections.

Executive Summary

The Executive Summary presents the primary Static-versus-Adaptive comparison under the current configuration.

It includes:

investigated alerts;

frauds detected;

frauds missed;

precision;

recall;

estimated operational cost;

cost difference between the two policies;

a concise policy interpretation.

Sequential results are treated as the primary operational evidence.

Analyst Capacity

The Analyst Capacity section shows how policy candidates move through the investigation process.

It includes:

investigated alerts;

suppressed alerts;

capacity-rejected alerts;

fraud investigation funnel;

analyst capacity by operational step;

fraud-risk analysis by transaction type;

a prioritised investigation queue;

transaction-level decision explanations.

The queue contains both investigated and non-investigated candidates so that the capacity cutoff can be inspected directly.

Sequential Workflow

The Sequential Workflow section documents the operational replay process and explains the distinction between the current simulation and a true production real-time system.

Monitoring

The Monitoring section divides the replay into consecutive reporting windows.

Monitoring windows are used only for reporting and trend inspection. They are separate from operational steps and do not control analyst-capacity resets.

The monitoring view reports:

candidate alerts;

investigated alerts;

capacity overflow;

missed frauds;

recall;

estimated operational cost.

This is operational monitoring of the offline replay. It is not an MLOps monitoring pipeline.

Sensitivity Analysis

Sensitivity analysis tests how the decision layer behaves when one operating parameter changes while the remaining settings are held constant.

The current experiments evaluate:

Parameter

Tested range or values

Transaction volume

1,000, 3,000, 10,000

Analyst capacity

Multiple alerts-per-step settings

Investigation cost

Multiple assumed cost values

Suppression window

Multiple step-based settings

Adaptive budget multiplier

Multiple multiplier settings

Static threshold

Multiple fraud-risk thresholds

Minimum Adaptive threshold

Multiple minimum fraud-risk thresholds

The sensitivity view includes:

a Decision Scenario Explorer;

baseline configuration;

Static-versus-Adaptive comparison across tested settings;

experiment-level drill-down;

recall and estimated-cost comparison;

interpretation of which policy is preferable under each configuration.

The experiments follow a one-parameter-at-a-time design.

Current Example Configuration

For the current 10,000-transaction sequential scenario with analyst capacity set to 50 alerts per operational step, the dashboard reports:

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

Under this configuration, the Adaptive policy produces higher recall and lower estimated operational cost.

These values are simulation results for the selected PaySim replay and should not be generalised to real banking environments.

Example Capacity Scenario

The Decision Scenario Explorer can be used to compare the effect of different analyst-capacity settings.

For example, increasing Adaptive capacity from 50 to 60 alerts per operational step produced the following results in the current tested scenario:

Outcome

50 per step

60 per step

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

This type of comparison is used to assess how operational resources affect fraud coverage and queue pressure.

Technology Stack

Area

Technology

Programming language

Python

Data processing

Pandas, NumPy

Machine learning

scikit-learn

API

FastAPI

Dashboard

Streamlit

Visualisation

Matplotlib, Streamlit charts

Model persistence

Joblib / persisted model artifacts

Version control

Git, GitHub

Application Structure

The project is organised around separate modelling, API, decision, simulation, and dashboard components.

A simplified view of the application structure is:

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

The exact repository layout may change as implementation components are refactored.

API

The Streamlit dashboard obtains simulation results from the FastAPI backend.

The current dashboard uses API endpoints for:

sequential policy evaluation;

Static-versus-Adaptive comparison;

transaction-level decision rows;

sensitivity analysis.

The API base URL is configured through the API_BASE_URL environment variable.

When no environment variable is provided, the local development configuration uses:

http://127.0.0.1:8002

Running Locally

1. Create and activate a virtual environment

Windows:

py -m venv .venv
.venv\Scripts\activate

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

2. Install dependencies

pip install -r requirements.txt

3. Add the PaySim dataset

Place the dataset at:

data/raw/AIML Dataset.csv

4. Start the FastAPI backend

py -m uvicorn app.api.main:app --reload --port 8002

5. Start the Streamlit application

py -m streamlit run app/streamlit_app.py

The Streamlit application and FastAPI backend must use the same API configuration.

Deployment

The Streamlit interface is publicly deployed as a research demonstration.

Deployment makes the dashboard accessible through a browser, but does not change the underlying evaluation method. The application still uses synthetic PaySim data and offline chronological replay.

The deployment should therefore not be interpreted as evidence of production banking integration, live payment validation, or real-time fraud operations.

Testing

The repository contains tests for core application and decision-layer behaviour.

The testing scope includes areas such as:

preprocessing;

model loading;

threshold logic;

cost logic;

suppression;

decision-engine behaviour;

API responses;

invalid-input handling.

The sequential backend also validates consistency between candidate, investigated, suppressed, and capacity-rejected alert counts.

Limitations

The current implementation has several important limitations.

Synthetic data

The evaluation uses PaySim rather than institution-specific banking data. The results demonstrate behaviour within the experimental framework and do not establish external validity on real financial transactions.

Offline replay

The Sequential workflow uses stored transactions processed in chronological order. It does not receive continuously arriving payment events.

Simplified analyst capacity

Analyst capacity is represented as a fixed number of alerts per operational step. Real investigation capacity would also depend on staffing, case complexity, working hours, and investigation duration.

Retrospective labels

Ground-truth fraud labels are available for evaluation after the simulated decision has been made. In a production environment, confirmed fraud outcomes would usually arrive with delay.

Experimental cost assumptions

Investigation cost and missed-fraud value are simulation assumptions. They are used to compare decision policies under identical conditions and should not be interpreted as observed financial losses.

Future Work

Potential extensions that remain outside the current implementation include:

evaluation with appropriately governed real transaction data;

integration with a live transaction stream;

explicit mapping between PaySim steps and real operational time;

delayed analyst-feedback integration;

monitoring for changes in transaction and fraud patterns;

more realistic analyst-capacity models;

richer false-positive and missed-fraud cost models;

comparison of additional alert-ranking strategies.

Research Context

This repository was developed as part of a Master's thesis investigating how fraud-risk predictions can support operational decisions when investigation resources are limited.

The main contribution is the integration of machine-learning scoring with a configurable decision layer that supports:

alert selection;

prioritisation;

suppression;

capacity-constrained investigation;

sequential evaluation;

operational monitoring;

sensitivity analysis.

The project therefore evaluates fraud detection from an operational perspective rather than treating the model probability as the final decision.

Disclaimer

This repository is a research prototype.

It does not process live banking transactions, does not use real customer payment identifiers, and is not intended for production fraud operations.

All reported financial values are experimental simulation estimates.
