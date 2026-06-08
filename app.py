import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib

# -----------------------------
# SAFE IMPORTS
# -----------------------------
try:
    import shap
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False

from langgraph.graph import StateGraph, END


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
# 🧠 FRAUD MODEL AGENT (REAL ML INFERENCE)
# =========================================================
def fraud_agent(state):
    try:
        if model is None:
            state["fraud_probability"] = 0.5
            return state

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

        return state

    except:
        state["fraud_probability"] = 0.5
        return state


# =========================================================
# 🧠 BEHAVIOR AGENT
# =========================================================
def behavior_agent(state):
    try:
        flags = []

        if state["amount"] > 20000:
            flags.append("HIGH_AMOUNT")

        if state["velocity"] > 10:
            flags.append("VELOCITY_SPIKE")

        if state["shared_device_count"] > 2:
            flags.append("DEVICE_SHARING")

        state["risk_flags"] = flags

        return state

    except:
        state["risk_flags"] = []
        return state


# =========================================================
# 🚨 ALERT GENERATION AGENT (AUTONOMOUS DECISION)
# =========================================================
def alert_agent(state):
    prob = state.get("fraud_probability", 0)
    flags = state.get("risk_flags", [])

    # 🔥 EMERGENT ALERT LOGIC
    score = prob + (0.1 * len(flags))

    if score >= 0.8:
        state["alert"] = "🚨 CRITICAL FRAUD ALERT"
        state["risk_level"] = "CRITICAL"

    elif score >= 0.5:
        state["alert"] = "⚠️ SUSPICIOUS TRANSACTION"
        state["risk_level"] = "MEDIUM"

    else:
        state["alert"] = "✅ NORMAL TRANSACTION"
        state["risk_level"] = "LOW"

    return state


# =========================================================
# 🕵️ SHAP EXPLAINER AGENT
# =========================================================
def shap_agent(state):
    try:
        if model is None or not SHAP_AVAILABLE:
            state["shap"] = "SHAP not available"
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

        top = sorted(impacts.items(), key=lambda x: abs(x[1]), reverse=True)[:3]

        state["shap"] = top

        return state

    except Exception as e:
        state["shap"] = str(e)
        return state


# =========================================================
# 🔗 LANGGRAPH BUILD
# =========================================================
def build_graph():
    builder = StateGraph(dict)

    builder.add_node("fraud_agent", fraud_agent)
    builder.add_node("behavior_agent", behavior_agent)
    builder.add_node("alert_agent", alert_agent)
    builder.add_node("shap_agent", shap_agent)

    builder.set_entry_point("fraud_agent")

    builder.add_edge("fraud_agent", "behavior_agent")
    builder.add_edge("behavior_agent", "alert_agent")
    builder.add_edge("alert_agent", "shap_agent")
    builder.add_edge("shap_agent", END)

    return builder.compile()


app = build_graph()


# =========================================================
# 🧾 STREAMLIT UI
# =========================================================
st.title("🏦 Enterprise Fraud Intelligence System")
st.write("🔥 Agentic AI Fraud Detection + SHAP Explanation System")

amount = st.number_input("Amount", 100, 100000, 5000)
velocity = st.slider("Velocity (7d)", 1, 50, 5)
avg_amount = st.number_input("Avg Amount (30d)", 100, 100000, 4500)
deviation = st.slider("Deviation Ratio", 0.1, 5.0, 1.0)
seconds = st.slider("Seconds since last txn", 10, 10000, 500)
device = st.slider("Shared Device Count", 0, 10, 0)


# =========================================================
# 🚀 RUN SYSTEM
# =========================================================
if st.button("Run Fraud Analysis"):

    state = {
        "amount": amount,
        "velocity": velocity,
        "avg_amount_30d": avg_amount,
        "amount_deviation_ratio": deviation,
        "seconds_since_last_txn": seconds,
        "shared_device_count": device
    }

    try:
        result = app.invoke(state)

    except Exception as e:
        result = {
            "fraud_probability": 0.5,
            "risk_level": "SYSTEM FALLBACK",
            "alert": "⚠️ ERROR FALLBACK",
            "error": str(e)
        }

    # -----------------------------
    # OUTPUT
    # -----------------------------
    st.subheader("🧠 Final Decision")

    st.write("Fraud Probability:", result.get("fraud_probability"))
    st.write("Risk Level:", result.get("risk_level"))
    st.write("Alert:", result.get("alert"))

    st.subheader("🚨 Risk Flags")
    st.write(result.get("risk_flags", []))

    st.subheader("🕵️ SHAP Explanation")
    st.write(result.get("shap"))
