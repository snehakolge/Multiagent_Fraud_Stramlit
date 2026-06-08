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
# LOAD MODEL SAFELY
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
# 🧠 AGENTS (CORE LOGIC)
# =========================================================

# 1️⃣ FRAUD DETECTION AGENT
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


# 2️⃣ BEHAVIOR ANALYSIS AGENT
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


# 3️⃣ INVESTIGATION AGENT (🔥 THIS MAKES IT AGENTIC)
def investigator_agent(state):
    try:
        prob = state.get("fraud_probability", 0)
        flags = state.get("risk_flags", [])

        plan = []

        if prob > 0.7:
            plan.append("Deep transaction history analysis required")

        if "VELOCITY_SPIKE" in flags:
            plan.append("Analyze last 50 transactions")

        if "DEVICE_SHARING" in flags:
            plan.append("Perform device graph mapping")

        state["investigation_plan"] = plan

        return state

    except:
        state["investigation_plan"] = ["Manual review required"]
        return state


# 4️⃣ COMPLIANCE AGENT (RBI/EWS)
def compliance_agent(state):
    try:
        prob = state.get("fraud_probability", 0)
        flags = state.get("risk_flags", [])

        if prob > 0.8 or len(flags) >= 2:
            state["compliance_status"] = "RBI EWS ALERT TRIGGERED"
        else:
            state["compliance_status"] = "NORMAL"

        return state

    except:
        state["compliance_status"] = "UNKNOWN"
        return state


# 5️⃣ DECISION AGENT
def decision_agent(state):
    try:
        prob = state.get("fraud_probability", 0)
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
# 🔗 LANGGRAPH BUILD (TRUE AGENTIC FLOW)
# =========================================================
from langgraph.graph import StateGraph

def build_graph():
    builder = StateGraph(dict)

    builder.add_node("fraud_agent", fraud_agent)
    builder.add_node("behavior_agent", behavior_agent)
    builder.add_node("investigator_agent", investigator_agent)
    builder.add_node("compliance_agent", compliance_agent)
    builder.add_node("decision_agent", decision_agent)

    builder.set_entry_point("fraud_agent")

    builder.add_edge("fraud_agent", "behavior_agent")


    # 🔥 CONDITIONAL ROUTING (KEY AGENTIC FEATURE)
    def route(state):
        if state.get("fraud_probability", 0) > 0.7:
            return "investigator_agent"
        else:
            return "compliance_agent"


    builder.add_conditional_edges(
        "behavior_agent",
        route,
        {
            "investigator_agent": "investigator_agent",
            "compliance_agent": "compliance_agent"
        }
    )

    builder.add_edge("investigator_agent", "compliance_agent")
    builder.add_edge("compliance_agent", "decision_agent")

    return builder.compile()


app = build_graph()


# =========================================================
# 🧾 STREAMLIT UI
# =========================================================
st.title("🏦 Enterprise Fraud Intelligence System")
st.write("🔥 True LangGraph Multi-Agent Fraud Detection System")


amount = st.number_input("Amount", 100, 100000, 5000)
velocity = st.slider("Velocity (7d)", 1, 50, 5)
avg_amount = st.number_input("Avg Amount (30d)", 100, 100000, 4500)
deviation = st.slider("Deviation Ratio", 0.1, 5.0, 1.0)
seconds = st.slider("Seconds since last txn", 10, 10000, 500)
device = st.slider("Shared Device Count", 0, 10, 0)


# =========================================================
# 🚀 RUN AGENTIC SYSTEM
# =========================================================
if st.button("Run Fraud Investigation"):

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
            "action": "MANUAL REVIEW",
            "error": str(e)
        }

    # -----------------------------
    # OUTPUT
    # -----------------------------
    st.subheader("🧠 Final Agent Output")

    st.write("Fraud Probability:", result.get("fraud_probability"))
    st.write("Risk Level:", result.get("risk_level"))
    st.write("Action:", result.get("action"))
    st.write("Compliance Status:", result.get("compliance_status"))

    st.subheader("🚨 Risk Flags")
    st.write(result.get("risk_flags", []))

    st.subheader("🕵️ Investigation Plan (AGENT OUTPUT)")
    st.write(result.get("investigation_plan", []))


    # -----------------------------
    # EXPLANATION LAYER
    # -----------------------------
    st.subheader("📌 Explanation Engine")

    explanations = []

    if amount > 20000:
        explanations.append("High transaction amount detected")

    if velocity > 10:
        explanations.append("Velocity spike detected")

    if device > 2:
        explanations.append("Multiple device linkage")

    if len(explanations) == 0:
        explanations.append("No anomalies detected")

    for e in explanations:
        st.write("•", e)


    # -----------------------------
    # SHAP (OPTIONAL SAFE)
    # -----------------------------
    st.subheader("📊 SHAP Analysis")

    if not SHAP_AVAILABLE or model is None:
        st.warning("SHAP not available or model not loaded")
    else:
        st.success("SHAP ready (optional mode)")
