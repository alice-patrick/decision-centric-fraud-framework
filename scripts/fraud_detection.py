from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "fraud_detection_model.pkl"


st.set_page_config(
    page_title="Fraud Detection App",
    page_icon="🚨",
    layout="centered",
)


@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file was not found at: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


try:
    model = load_model()
except Exception as error:
    st.error(f"Could not load model: {error}")
    st.stop()


st.title("Fraud Detection Prediction App")

st.markdown(
    "Enter the transaction details to estimate whether the transaction "
    "is fraudulent or legitimate."
)

st.divider()


transaction_type = st.selectbox(
    "Transaction Type",
    [
        "PAYMENT",
        "TRANSFER",
        "CASH_OUT",
        "DEBIT",
        "CASH_IN",
    ],
)

amount = st.number_input(
    "Amount",
    min_value=0.0,
    value=1000.0,
    step=100.0,
)

old_balance_origin = st.number_input(
    "Old Balance (Sender)",
    min_value=0.0,
    value=1000.0,
    step=100.0,
)

new_balance_origin = st.number_input(
    "New Balance (Sender)",
    min_value=0.0,
    value=0.0,
    step=100.0,
)

old_balance_destination = st.number_input(
    "Old Balance (Receiver)",
    min_value=0.0,
    value=0.0,
    step=100.0,
)

new_balance_destination = st.number_input(
    "New Balance (Receiver)",
    min_value=0.0,
    value=0.0,
    step=100.0,
)


if st.button("Predict", type="primary"):

    input_data = pd.DataFrame(
        {
            "type": [transaction_type],
            "amount": [amount],
            "oldbalanceOrg": [old_balance_origin],
            "newbalanceOrig": [new_balance_origin],
            "oldbalanceDest": [old_balance_destination],
            "newbalanceDest": [new_balance_destination],
        }
    )

    try:
        prediction = int(model.predict(input_data)[0])

        fraud_probability = None

        if hasattr(model, "predict_proba"):
            fraud_probability = float(
                model.predict_proba(input_data)[0][1]
            )

        st.divider()
        st.subheader("Prediction Result")

        if fraud_probability is not None:
            st.metric(
                label="Fraud Probability",
                value=f"{fraud_probability:.2%}",
            )

        if prediction == 1:
            st.error(
                "The transaction is predicted to be fraudulent."
            )
        else:
            st.success(
                "The transaction is predicted to be legitimate."
            )

        with st.expander("View input data"):
            st.dataframe(
                input_data,
                use_container_width=True,
            )

    except Exception as error:
        st.error(f"Prediction failed: {error}")

        st.write("Input data:")

        st.dataframe(
            input_data,
            use_container_width=True,
        )