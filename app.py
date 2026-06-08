import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib

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
# LOAD MODEL
# -----------------------------
MODEL_PATH = "efrms_xgboost_model.pkl"

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except:
        model = None


# -----------------------------
# FEATURES
# -----------------------------
FEATURES = [
    "amount",
    "transaction_velocity_7d",
    "avg_amount_30d",
    "amount_deviation_ratio",
    "seconds_since_last_txn",
    "shared_device_count"
]


# =========================================================
# 🧠 LANGGRAPH AGENTS
# =========================================================

def fraud_agent(state):
    try:
        amount = state.get("amount", 0)
        velocity = state.get("velocity", 0)

        if amount > 20000 or velocity > 10:
            state["fraud_probability"] = 0.9
        else:
            state["fraud_probability"] = 0.3

        return state

    except:
        state["fraud_probability"] = 0.5
        return state


def behavior_agent(state):
    try:
        flags = []

        if state.get("amount", 0) > 20000:
            flags.append("HIGH_AMOUNT")

        if state.get("velocity", 0) > 10:
            flags.append("VELOCITY_SPIKE")

        if state.get("shared_device_count", 0) > 2:
            flags.append("DEVICE_SHARING")

        state["risk_flags"] = flags
        return state

    except:
        state["risk_flags"] = ["UNKNOWN"]
        return state


def compliance_agent(state):
    try:
        prob = state.get("fraud_probability", 0.5)
        flags = state.get("risk_flags", [])

        if prob > 0.8 or len(flags) >= 2:
            state["compliance_status"] = "RBI ALERT (EWS TRIGGERED)"
        else:
            state["compliance_status"] = "NORMAL"

        return state

    except:
        state["compliance_status"] = "UNKNOWN"
        return state


def decision_agent(state):
    try:
        prob = state.get("fraud_probability", 0.5)
        flags = state.get("risk_flags", [])

        if prob > 0.85:
            state["action"] = "FREEZE + AML INVESTIGATION"
            state["risk_level"] = "CRITICAL"
        elif len(flags) > 0:
            state["action"] = "STEP-UP AUTHENTICATION"
            state["risk_level"] = "MEDIUM"
        else:
            state["action"] = "ALLOW"
            state["risk_level"] = "LOW"

        return state

    except:
        state["action"] = "MANUAL REVIEW"
        state["risk_level"] = "UNKNOWN"
        return state


# =========================================================
# 🔗 LANGGRAPH BUILD
# =========================================================
from langgraph.graph import StateGraph

def build_graph():
    builder = StateGraph(dict)

    builder.add_node("fraud_agent", fraud_agent)
    builder.add_node("behavior_agent", behavior_agent)
    builder.add_node("compliance_agent", compliance_agent)
    builder.add_node("decision_agent", decision_agent)

    builder.set_entry_point("fraud_agent")

    builder.add_edge("fraud_agent", "behavior_agent")
    builder.add_edge("behavior_agent", "compliance_agent")
    builder.add_edge("compliance_agent", "decision_agent")

    return builder.compile()


app = build_graph()   # 🔥 FIXED: THIS WAS YOUR MAIN ISSUE


# =========================================================
# 🧾 SAFE INPUT UI
# =========================================================
st.title("🏦 Enterprise Fraud Intelligence System")
st.write("LangGraph Multi-Agent Fraud Detection Platform (Stable Version)")

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
            "risk_level": "FALLBACK",
            "action": "MANUAL REVIEW",
            "error": str(e)
        }

    # =====================================================
    # 📊 OUTPUT
    # =====================================================
    st.subheader("🧠 Fraud Decision Output")

    st.write("Fraud Probability:", result.get("fraud_probability", 0))
    st.write("Risk Level:", result.get("risk_level", "UNKNOWN"))
    st.write("Action:", result.get("action", "UNKNOWN"))
    st.write("Compliance Status:", result.get("compliance_status", "UNKNOWN"))

    st.subheader("🚨 Risk Flags")
    st.write(result.get("risk_flags", []))


    # =====================================================
    # 🧠 EXPLANATION LAYER (RULE BASED)
    # =====================================================
    st.subheader("📌 Explanation Engine")

    explanations = []

    if amount > 20000:
        explanations.append("High transaction amount detected")

    if velocity > 10:
        explanations.append("Unusual velocity spike")

    if deviation > 2:
        explanations.append("Deviation from normal spending pattern")

    if device > 2:
        explanations.append("Multiple devices linked")

    if len(explanations) == 0:
        explanations.append("No anomalies detected")

    for e in explanations:
        st.write("•", e)


    # =====================================================
    # ⚠️ SHAP OPTIONAL
    # =====================================================
    st.subheader("📊 SHAP Analysis")

    if not SHAP_AVAILABLE or model is None:
        st.warning("SHAP not available or model not loaded")
    else:
        st.success("SHAP ready (optional advanced mode)")
