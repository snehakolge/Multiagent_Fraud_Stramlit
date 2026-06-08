import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib

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
# 🧠 1. FRAUD MODEL AGENT (REAL ML)
# =========================================================
def fraud_agent(state):
    try:
        if model is None:
            state["fraud_probability"] = 0.5
            return state

        df = pd.DataFrame([{
            "amount": state.get("amount", 0),
            "transaction_velocity_7d": state.get("velocity", 0),
            "avg_amount_30d": state.get("avg_amount_30d", 0),
            "amount_deviation_ratio": state.get("amount_deviation_ratio", 0),
            "seconds_since_last_txn": state.get("seconds_since_last_txn", 0),
            "shared_device_count": state.get("shared_device_count", 0)
        }])

        prob = model.predict_proba(df)[0][1]
        state["fraud_probability"] = float(prob)

        return state

    except:
        state["fraud_probability"] = 0.5
        return state


# =========================================================
# 🧠 2. SIGNAL AGENT (BEHAVIOR PATTERNS)
# =========================================================
def behavior_agent(state):
    flags = []

    if state.get("amount", 0) > 20000:
        flags.append("HIGH_AMOUNT")

    if state.get("velocity", 0) > 10:
        flags.append("VELOCITY_SPIKE")

    if state.get("shared_device_count", 0) > 2:
        flags.append("DEVICE_SHARING")

    state["risk_flags"] = flags
    return state


# =========================================================
# 🧠 3. RISK SCORING AGENT (IMPORTANT - MAKES IT “EMERGENT”)
# =========================================================
def scoring_agent(state):
    prob = state.get("fraud_probability", 0)
    flags = state.get("risk_flags", [])

    score = prob + (0.08 * len(flags))

    state["risk_score"] = min(score, 1.0)
    return state


# =========================================================
# 🚨 4. ALERT AGENT (AUTO GENERATION)
# =========================================================
def alert_agent(state):
    score = state.get("risk_score", 0)

    if score >= 0.75:
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
# 🕵️ 5. SHAP EXPLAINER (SAFE)
# =========================================================
def shap_agent(state):
    try:
        if model is None or not SHAP_AVAILABLE:
            state["shap"] = ["SHAP not available"]
            return state

        df = pd.DataFrame([{
            "amount": state.get("amount", 0),
            "transaction_velocity_7d": state.get("velocity", 0),
            "avg_amount_30d": state.get("avg_amount_30d", 0),
            "amount_deviation_ratio": state.get("amount_deviation_ratio", 0),
            "seconds_since_last_txn": state.get("seconds_since_last_txn", 0),
            "shared_device_count": state.get("shared_device_count", 0)
        }])

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df)

        impacts = dict(zip(df.columns, shap_values[0]))

        top_features = sorted(
            impacts.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:3]

        state["shap"] = top_features

        return state

    except:
        state["shap"] = ["SHAP error"]
        return state


# =========================================================
# 🧠 6. FINAL DECISION AGENT (REAL BRAIN)
# =========================================================
def final_agent(state):
    score = state.get("risk_score", 0)

    if score >= 0.75:
        state["decision"] = "FREEZE ACCOUNT + AML ALERT"
    elif score >= 0.5:
        state["decision"] = "STEP-UP AUTHENTICATION"
    else:
        state["decision"] = "ALLOW TRANSACTION"

    return state


# =========================================================
# 🔗 LANGGRAPH FLOW
# =========================================================
def build_graph():
    builder = StateGraph(dict)

    builder.add_node("fraud_agent", fraud_agent)
    builder.add_node("behavior_agent", behavior_agent)
    builder.add_node("scoring_agent", scoring_agent)
    builder.add_node("alert_agent", alert_agent)
    builder.add_node("shap_agent", shap_agent)
    builder.add_node("final_agent", final_agent)

    builder.set_entry_point("fraud_agent")

    builder.add_edge("fraud_agent", "behavior_agent")
    builder.add_edge("behavior_agent", "scoring_agent")
    builder.add_edge("scoring_agent", "alert_agent")
    builder.add_edge("alert_agent", "shap_agent")
    builder.add_edge("shap_agent", "final_agent")
    builder.add_edge("final_agent", END)

    return builder.compile()


app = build_graph()


# =========================================================
# 🧾 STREAMLIT UI
# =========================================================
st.title("🏦 Enterprise Fraud Intelligence System")
st.write("Agentic ML + SHAP + Automated Fraud Alerts")

amount = st.number_input("Amount", 100, 100000, 5000)
velocity = st.slider("Velocity (7d)", 1, 50, 5)
avg_amount = st.number_input("Avg Amount (30d)", 100, 100000, 4500)
deviation = st.slider("Deviation Ratio", 0.1, 5.0, 1.0)
seconds = st.slider("Seconds since last txn", 10, 10000, 500)
device = st.slider("Shared Device Count", 0, 10, 0)


# =========================================================
# 🚀 RUN SYSTEM
# =========================================================
if st.button("Analyze Transaction"):

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
            "alert": "ERROR",
            "decision": "MANUAL REVIEW",
            "error": str(e)
        }

    # -----------------------------
    # OUTPUT
    # -----------------------------
    st.subheader("🧠 Final Output")

    st.write("Fraud Probability:", result.get("fraud_probability"))
    st.write("Risk Score:", result.get("risk_score"))
    st.write("Risk Level:", result.get("risk_level"))
    st.write("Alert:", result.get("alert"))
    st.write("Decision:", result.get("decision"))

    st.subheader("🚨 Risk Flags")
    st.write(result.get("risk_flags", []))

    st.subheader("🕵️ SHAP Explanation")
    st.write(result.get("shap"))
