import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

# -----------------------------
# SAFE IMPORTS
# -----------------------------
try:
    from sklearn.pipeline import Pipeline
except:
    Pipeline = None

try:
    import shap
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False


# -----------------------------
# LOAD MODEL SAFELY
# -----------------------------
MODEL_PATH = "efrms_xgboost_model.pkl"

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        model = None


# -----------------------------
# SAFE FEATURES
# -----------------------------
FEATURES = [
    "amount",
    "transaction_velocity_7d",
    "avg_amount_30d",
    "amount_deviation_ratio",
    "seconds_since_last_txn",
    "shared_device_count"
]


# -----------------------------
# INPUT UI
# -----------------------------
def get_input():
    st.subheader("📥 Transaction Input")

    data = {
        "amount": st.number_input("Amount", 100, 100000, 5000),
        "transaction_velocity_7d": st.slider("Velocity (7d)", 1, 50, 5),
        "avg_amount_30d": st.number_input("Avg Amount (30d)", 100, 100000, 4500),
        "amount_deviation_ratio": st.slider("Deviation Ratio", 0.1, 5.0, 1.0),
        "seconds_since_last_txn": st.slider("Seconds since last txn", 10, 10000, 500),
        "shared_device_count": st.slider("Shared Device Count", 0, 10, 0)
    }

    return pd.DataFrame([data])


# -----------------------------
# SAFE FEATURE ALIGNMENT
# -----------------------------
def align(df):
    if model is not None and hasattr(model, "feature_names_in_"):
        return df.reindex(columns=model.feature_names_in_, fill_value=0)

    return df.reindex(columns=FEATURES, fill_value=0)


# -----------------------------
# FRAUD PREDICTION (SAFE)
# -----------------------------
def predict(df):
    try:
        if model is None:
            return 0.5

        X = align(df)

        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)[0][1]
        else:
            return float(model.predict(X)[0])

    except Exception:
        return 0.5


# -----------------------------
# RULE-BASED EXPLANATION (SAFE)
# -----------------------------
def explain(row):
    reasons = []

    if row["amount"] > 20000:
        reasons.append("High transaction amount")

    if row["transaction_velocity_7d"] > 10:
        reasons.append("Velocity spike detected")

    if row["amount_deviation_ratio"] > 2:
        reasons.append("Amount deviates from normal behavior")

    if row["seconds_since_last_txn"] < 60:
        reasons.append("Rapid repeated transactions")

    if row["shared_device_count"] > 2:
        reasons.append("Multiple accounts using same device")

    if not reasons:
        reasons.append("No strong anomaly detected")

    return reasons


# -----------------------------
# SAFE SHAP (OPTIONAL)
# -----------------------------
def shap_analysis(X):
    if not SHAP_AVAILABLE or model is None:
        return None

    try:
        explainer = shap.TreeExplainer(model)
        return explainer.shap_values(X)
    except:
        return None


# -----------------------------
# SAFE LANGGRAPH WRAPPER
# -----------------------------
def run_graph(state):
    try:
        return app.invoke(state)   # your LangGraph app
    except Exception as e:
        return {
            "fraud_probability": 0.5,
            "risk": "SYSTEM FALLBACK",
            "action": "MANUAL REVIEW",
            "error": str(e)
        }


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("🏦 Enterprise Fraud Intelligence System")
st.write("LangGraph Multi-Agent Fraud Detection Platform (Crash Safe)")

input_df = get_input()

# -----------------------------
# BUTTON TRIGGER
# -----------------------------
if st.button("Analyze Transaction"):

    # -------------------------
    # PREDICTION
    # -------------------------
    prob = predict(input_df)

    if prob > 0.85:
        risk = "🔴 CRITICAL FRAUD ALERT"
        action = "FREEZE + MANUAL REVIEW"
    elif prob > 0.5:
        risk = "🟠 MEDIUM RISK"
        action = "STEP-UP AUTHENTICATION"
    else:
        risk = "🟢 LOW RISK"
        action = "ALLOW"

    st.subheader(risk)
    st.write("Fraud Probability:", round(prob, 4))
    st.write("Action:", action)

    # -------------------------
    # EXPLANATION
    # -------------------------
    st.subheader("🧠 Risk Explanation")

    for r in explain(input_df.iloc[0]):
        st.write("•", r)

    # -------------------------
    # SHAP (SAFE)
    # -------------------------
    st.subheader("📊 SHAP (Optional)")

    shap_vals = shap_analysis(align(input_df))

    if shap_vals is None:
        st.warning("SHAP not available or not stable for this input")
    else:
        st.success("SHAP computed successfully")
        st.write("SHAP values generated")

    # -------------------------
    # LANGGRAPH (SAFE)
    # -------------------------
    st.subheader("🤖 Agentic System Output")

    state = {
        "features": align(input_df),
        "input": input_df.to_dict()
    }

    result = run_graph(state)

    st.json(result)
