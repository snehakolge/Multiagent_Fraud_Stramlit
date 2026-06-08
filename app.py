import streamlit as st
import pandas as pd
import numpy as np
import time
import joblib
import os

from langgraph.graph import StateGraph, END

# -----------------------------
# OPTIONAL SHAP
# -----------------------------
try:
    import shap
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False


# -----------------------------
# LOAD MODEL
# -----------------------------
MODEL_PATH = "efrms_xgboost_model.pkl"

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except:
        model = None


# =========================================================
# 🧠 FRAUD AGENT (ML SIGNAL)
# =========================================================
def fraud_agent(state):
    if model:
        df = pd.DataFrame([{
            "amount": state["amount"],
            "transaction_velocity_7d": state["velocity"],
            "avg_amount_30d": state["avg_amount_30d"],
            "amount_deviation_ratio": state["amount_deviation_ratio"],
            "seconds_since_last_txn": state["seconds_since_last_txn"],
            "shared_device_count": state["shared_device_count"]
        }])

        prob = model.predict_proba(df)[0][1]
        state["fraud_probability"] = float(prob)
    else:
        state["fraud_probability"] = min(1.0, state["amount"] / 100000)

    return state


# =========================================================
# 🧠 BEHAVIOR AGENT
# =========================================================
def behavior_agent(state):
    flags = []

    if state["amount"] > 20000:
        flags.append("HIGH_AMOUNT")

    if state["velocity"] > 10:
        flags.append("VELOCITY_SPIKE")

    if state["shared_device_count"] > 2:
        flags.append("DEVICE_SHARING")

    state["risk_flags"] = flags
    return state


# =========================================================
# 🧠 SCORING AGENT
# =========================================================
def scoring_agent(state):
    score = state["fraud_probability"] + 0.1 * len(state["risk_flags"])
    state["risk_score"] = min(score, 1.0)
    return state


# =========================================================
# 🚨 ALERT AGENT (AUTOMATIC DECISION ENGINE)
# =========================================================
def alert_agent(state):
    score = state["risk_score"]

    if score >= 0.75:
        state["alert"] = "🚨 FRAUD ALERT - AUTO FREEZE TRIGGERED"
        state["action"] = "FREEZE_ACCOUNT"
        state["severity"] = "CRITICAL"

    elif score >= 0.5:
        state["alert"] = "⚠️ SUSPICIOUS ACTIVITY DETECTED"
        state["action"] = "STEP_UP_AUTH"
        state["severity"] = "MEDIUM"

    else:
        state["alert"] = "✅ NORMAL TRANSACTION"
        state["action"] = "ALLOW"
        state["severity"] = "LOW"

    return state


# =========================================================
# 🕵️ SHAP EXPLAINER (SAFE)
# =========================================================
def shap_agent(state):
    try:
        if not model or not SHAP_AVAILABLE:
            state["shap"] = ["SHAP not available"]
            return state

        df = pd.DataFrame([{
            "amount": state["amount"],
            "transaction_velocity_7d": state["velocity"],
            "avg_amount_30d": state["avg_amount_30d"],
            "amount_deviation_ratio": state["amount_deviation_ratio"],
            "seconds_since_last_txn": state["seconds_since_last_txn"],
            "shared_device_count": state["shared_device_count"]
        }])

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df)

        impacts = dict(zip(df.columns, shap_values[0]))

        state["shap"] = sorted(
            impacts.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]

    except:
        state["shap"] = ["SHAP error"]

    return state


# =========================================================
# FINAL AGENT (CASE CREATION)
# =========================================================
def case_agent(state):
    state["case_id"] = f"CASE-{int(time.time())}"

    if state["risk_score"] >= 0.75:
        state["case_status"] = "OPEN - CRITICAL"
    elif state["risk_score"] >= 0.5:
        state["case_status"] = "OPEN - REVIEW"
    else:
        state["case_status"] = "CLOSED - SAFE"

    return state


# =========================================================
# LANGGRAPH PIPELINE
# =========================================================
def build_graph():
    builder = StateGraph(dict)

    builder.add_node("fraud_agent", fraud_agent)
    builder.add_node("behavior_agent", behavior_agent)
    builder.add_node("scoring_agent", scoring_agent)
    builder.add_node("alert_agent", alert_agent)
    builder.add_node("shap_agent", shap_agent)
    builder.add_node("case_agent", case_agent)

    builder.set_entry_point("fraud_agent")

    builder.add_edge("fraud_agent", "behavior_agent")
    builder.add_edge("behavior_agent", "scoring_agent")
    builder.add_edge("scoring_agent", "alert_agent")
    builder.add_edge("alert_agent", "shap_agent")
    builder.add_edge("shap_agent", "case_agent")
    builder.add_edge("case_agent", END)

    return builder.compile()


app = build_graph()


# =========================================================
# 🏦 STREAMLIT CONTROL TOWER UI
# =========================================================
st.title("🏦 Fraud Control Tower - Real Time System")
st.write("🔥 Always-On Agentic Fraud Monitoring System")

amount = st.number_input("Amount", 100, 100000, 5000)
velocity = st.slider("Velocity", 1, 50, 5)
avg_amount = st.number_input("Avg Amount", 100, 100000, 4500)
deviation = st.slider("Deviation Ratio", 0.1, 5.0, 1.0)
seconds = st.slider("Seconds Since Last Txn", 10, 10000, 500)
device = st.slider("Shared Device Count", 0, 10, 0)


# =========================================================
# 🔄 AUTO MONITORING MODE (KEY FEATURE)
# =========================================================
st.subheader("🔄 Real-Time Monitoring Mode")

run_stream = st.checkbox("Enable Live Monitoring Simulation")

if run_stream:

    placeholder = st.empty()

    for i in range(3):  # simulate stream batches

        state = {
            "amount": np.random.randint(1000, 50000),
            "velocity": np.random.randint(1, 30),
            "avg_amount_30d": 4500,
            "amount_deviation_ratio": np.random.random() * 3,
            "seconds_since_last_txn": np.random.randint(10, 1000),
            "shared_device_count": np.random.randint(0, 5)
        }

        result = app.invoke(state)

        with placeholder.container():

            st.markdown("## 🚨 LIVE TRANSACTION ANALYSIS")

            st.write("Amount:", result["amount"])
            st.write("Fraud Probability:", result["fraud_probability"])
            st.write("Risk Score:", result["risk_score"])
            st.write("Alert:", result["alert"])
            st.write("Action:", result["action"])
            st.write("Case ID:", result["case_id"])
            st.write("Case Status:", result["case_status"])

            st.write("Risk Flags:", result["risk_flags"])
            st.write("SHAP:", result["shap"])

        time.sleep(2)

else:

    if st.button("Analyze Single Transaction"):

        state = {
            "amount": amount,
            "velocity": velocity,
            "avg_amount_30d": avg_amount,
            "amount_deviation_ratio": deviation,
            "seconds_since_last_txn": seconds,
            "shared_device_count": device
        }

        result = app.invoke(state)

        st.subheader("🧠 FINAL OUTPUT")

        st.write(result)
