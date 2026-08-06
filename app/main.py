from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.config_loader import load_config
from app.core.registry import load_model_registry, get_active_model_info
from app.model.save_load import load_model
from app.model.predict import predict_proba
from app.core.logger import write_json_log
from decisioning.decision_engine import make_decision
from app.monitoring.metrics_tracker import calculate_monitoring_metrics


app = FastAPI(title="Fraud Detection Decision System")


class TransactionRequest(BaseModel):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    current_alert_rate: float = 0.05
    mode: str = "adaptive"


@app.on_event("startup")
def startup_event():
    config = load_config()
    registry = load_model_registry(config["model"]["registry_path"])
    model_info = get_active_model_info(registry)
    model = load_model(model_info["path"])

    app.state.config = config
    app.state.registry = registry
    app.state.model = model
    app.state.model_info = model_info


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "active_model": app.state.registry["active_model"],
    }

@app.get("/metrics")
def get_metrics():
    return calculate_monitoring_metrics(app.state.config)

@app.post("/predict-and-decide")
def predict_and_decide(transaction: TransactionRequest):
    transaction_dict = transaction.model_dump()

    mode = transaction_dict.pop("mode")
    current_alert_rate = transaction_dict.pop("current_alert_rate")

    score = predict_proba(app.state.model, transaction_dict)

    decision_result = make_decision(
        score=score,
        amount=transaction_dict["amount"],
        config=app.state.config,
        mode=mode,
        current_alert_rate=current_alert_rate,
    )

    response = {
        "transaction": transaction_dict,
        "model": {
            "model_version": app.state.registry["active_model"],
            "fraud_score": score,
        },
        "decision": decision_result,
    }

    write_json_log(
        log_filename=app.state.config["logging"]["predictions_log_path"],
        payload=response,
    )

    if decision_result["decision"] == "alert":
        write_json_log(
            log_filename=app.state.config["logging"]["alerts_log_path"],
            payload=response,
        )

    return response