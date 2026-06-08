import streamlit as st
import pandas as pd
import numpy as np
import time
import joblib
import os

from langgraph.graph import StateGraph, END

# -------------------------
# MODEL
# -------------------------
model = None
if os.path.exists("efrms_xgboost_model.pkl"):
    model = joblib.load("efrms_xgboost_model.pkl")


# =========================
# 🧠 FRAUD AGENT
# =========================
def fraud_agent(state):
    if model:
        df = pd.DataFrame([state])
        state["ml_score"] = float(model.predict_proba(df)[0][1])
    else:
        state["ml_score"] = state["amount"] / 100000
    return state


# =========================
# 🧠 BEHAVIOR AGENT
# =========================
def behavior_agent(state):
    flags = []

    if state["amount"] > 20000:
        flags.append("HIGH_AMOUNT")
    if state["velocity"] > 10:
        flags.append("VELOCITY_SPIKE")
    if state["shared_device_count"] > 2:
        flags.append("DEVICE_SHARING")

    state["flags"] = flags
    state["behavior_score"] = len(flags) * 0.25
    return state


# =========================
# 🧠 SCORING
# =========================
def scoring_agent(state):
    state["risk_score"] = min(
        state["ml_score"] + state["behavior_score"],
        1.0
    )
    return state


# =========================
# 🚨 ALERT ENGINE (AUTONOMOUS)
# =========================
def alert_agent(state):

    if state["risk_score"] > 0.75:
        state["alert"] = "🚨 FRAUD ALERT AUTO-GENERATED"
        state["action"] = "FREEZE"
    elif state["risk_score"] > 0.5:
        state["alert"] = "⚠️ SUSPICIOUS TRANSACTION AUTO-FLAGGED"
        state["action"] = "REVIEW"
    else:
        state["alert"] = "✅ SAFE"
        state["action"] = "ALLOW"

    return state


# =========================
# GRAPH
# =========================
def build_graph():
    g = StateGraph(dict)

    g.add_node("fraud_agent", fraud_agent)
    g.add_node("behavior_agent", behavior_agent)
    g.add_node("scoring_agent", scoring_agent)
    g.add_node("alert_agent", alert_agent)

    g.set_entry_point("fraud_agent")

    g.add_edge("fraud_agent", "behavior_agent")
    g.add_edge("behavior_agent", "scoring_agent")
    g.add_edge("scoring_agent", "alert_agent")
    g.add_edge("alert_agent", END)

    return g.compile()


app = build_graph()


# =========================
# UI (NO BUTTON = AUTO SYSTEM)
# =========================
st.title("🏦 LIVE Fraud Control Tower (Auto Agent System)")
st.write("🔄 System continuously monitoring transactions...")

placeholder = st.empty()

# =========================
# 🔥 CONTINUOUS STREAM LOOP
# =========================
for i in range(50):  # simulate live transactions

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

        st.subheader("🔴 LIVE TRANSACTION FEED")

        st.write("Amount:", result["amount"])
        st.write("ML Score:", round(result["ml_score"], 3))
        st.write("Risk Score:", round(result["risk_score"], 3))
        st.write("Flags:", result["flags"])
        st.write("Alert:", result["alert"])
        st.write("Action:", result["action"])

    time.sleep(1)
