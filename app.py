import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

from langgraph.graph import StateGraph, END

# -----------------------
# MODEL
# -----------------------
model = None
if os.path.exists("efrms_xgboost_model.pkl"):
    model = joblib.load("efrms_xgboost_model.pkl")


# =========================
# 🧠 FRAUD ML AGENT
# =========================
def fraud_agent(state):
    if model:
        df = pd.DataFrame([state])
        prob = model.predict_proba(df)[0][1]
    else:
        prob = state["amount"] / 100000

    state["ml_score"] = float(prob)
    return state


# =========================
# 🧠 RULES AGENT
# =========================
def rules_agent(state):
    score = 0

    if state["amount"] > 20000:
        score += 0.4
    if state["velocity"] > 10:
        score += 0.3
    if state["shared_device_count"] > 2:
        score += 0.3

    state["rule_score"] = min(score, 1.0)
    return state


# =========================
# 🧠 BEHAVIOR AGENT
# =========================
def behavior_agent(state):
    anomalies = []

    if state["amount"] > state["avg_amount_30d"] * 3:
        anomalies.append("SPEND_SPIKE")

    if state["seconds_since_last_txn"] < 30:
        anomalies.append("RAPID_TXN")

    state["behavior_flags"] = anomalies
    state["behavior_score"] = len(anomalies) * 0.3

    return state


# =========================
# 🧠 ANOMALY AGENT
# =========================
def anomaly_agent(state):
    score = np.random.uniform(0.1, 0.6)  # simulated anomaly engine
    state["anomaly_score"] = score
    return state


# =========================
# 🧠 JUDGE AGENT (REAL BRAIN)
# =========================
def judge_agent(state):

    ml = state.get("ml_score", 0)
    rule = state.get("rule_score", 0)
    beh = state.get("behavior_score", 0)
    ano = state.get("anomaly_score", 0)

    # weighted voting system
    final_score = (
        0.4 * ml +
        0.25 * rule +
        0.2 * beh +
        0.15 * ano
    )

    state["final_score"] = final_score

    if final_score > 0.75:
        state["decision"] = "🚨 FRAUD CONFIRMED"
    elif final_score > 0.5:
        state["decision"] = "⚠️ SUSPICIOUS - REVIEW"
    else:
        state["decision"] = "✅ SAFE"

    # 👇 THIS is what makes it agentic (reasoning trace)
    state["reasoning_trace"] = {
        "ml_agent": ml,
        "rule_agent": rule,
        "behavior_agent": beh,
        "anomaly_agent": ano,
        "judge_score": final_score
    }

    return state


# =========================
# GRAPH
# =========================
def build_graph():
    g = StateGraph(dict)

    g.add_node("fraud_agent", fraud_agent)
    g.add_node("rules_agent", rules_agent)
    g.add_node("behavior_agent", behavior_agent)
    g.add_node("anomaly_agent", anomaly_agent)
    g.add_node("judge_agent", judge_agent)

    g.set_entry_point("fraud_agent")

    g.add_edge("fraud_agent", "rules_agent")
    g.add_edge("rules_agent", "behavior_agent")
    g.add_edge("behavior_agent", "anomaly_agent")
    g.add_edge("anomaly_agent", "judge_agent")
    g.add_edge("judge_agent", END)

    return g.compile()


app = build_graph()


# =========================
# UI
# =========================
st.title("🏦 TRUE Agentic Fraud System (Debate AI)")

amount = st.number_input("Amount", 100, 100000, 5000)
velocity = st.slider("Velocity", 1, 50, 5)
avg_amount_30d = st.number_input("Avg Amount 30d", 100, 100000, 4500)
shared_device_count = st.slider("Shared Devices", 0, 10, 0)
seconds_since_last_txn = st.slider("Seconds Since Last Txn", 10, 10000, 500)

if st.button("Run Agent Debate System"):

    state = {
        "amount": amount,
        "velocity": velocity,
        "avg_amount_30d": avg_amount_30d,
        "shared_device_count": shared_device_count,
        "seconds_since_last_txn": seconds_since_last_txn
    }

    result = app.invoke(state)

    st.subheader("🧠 FINAL DECISION")
    st.write(result["decision"])

    st.subheader("⚖️ AGENT DEBATE RESULTS")
    st.json(result["reasoning_trace"])

    st.subheader("📊 FINAL SCORE")
    st.write(result["final_score"])
