import pandas as pd


def predict_proba(model, features: dict) -> float:
    df = pd.DataFrame([features])
    proba = model.predict_proba(df)[0][1]
    return float(proba)