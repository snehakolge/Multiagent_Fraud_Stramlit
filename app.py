import streamlit as st
import random
import uuid
import time

# =========================
# 🟢 VELOCITY AGENT
# =========================
def velocity_agent(txn):
    v = txn["velocity_7d"]

    if v > 40:
        return "CRITICAL", f"Extreme burst: {v} txns/7d"
    elif v > 20:
        return "SUSPICIOUS", f"High activity: {v} txns/7d"
    else:
        return "NORMAL", f"Normal velocity: {v}"


# =========================
# 🟡 PATTERN AGENT
# =========================
def pattern_agent(txn):
    dev = txn["amount_deviation"]

    if dev > 3:
        return "SUSPICIOUS", f"Severe deviation: {dev:.2f}x baseline"
    elif dev > 1.5:
        return "WATCHLIST", f"Moderate deviation: {dev:.2f}x baseline"
    else:
        return "NORMAL", f"Stable behavior: {dev:.2f}x"


# =========================
# 🔵 ML AGENT
# =========================
def ml_agent(txn):
    score = txn["ml_score"]

    if score > 0.8:
        return "HIGH_RISK", f"Fraud probability: {score:.2f}"
    elif score > 0.4:
        return "MEDIUM_RISK", f"Moderate risk: {score:.2f}"
    else:
        return "LOW_RISK", f"Low risk: {score:.2f}"


# =========================
# 🟣 RBI RULE AGENT
# =========================
def rbi_agent(txn):
    flags = txn["flags"]

    if "VELOCITY_SPIKE" in flags and txn["amount"] > 10000:
        return "HIGH_RISK_RULE", "RBI EWS: velocity spike + high value txn"
    elif "FAILED_TXN" in flags:
        return "MEDIUM_RISK_RULE", "RBI EWS: multiple failed transactions"
    else:
        return "CLEAR", "No RBI rule triggered"


# =========================
# 🧠 META ORCHESTRATOR (IMPORTANT UPGRADE)
# =========================
def orchestrator(v, p, m, r):

    risk_score = 0
    priority_flags = []

    # 🟣 RBI OVERRIDE (HIGHEST PRIORITY)
    if r[0] == "HIGH_RISK_RULE":
        risk_score += 60
        priority_flags.append("RBI_OVERRIDE")

    elif r[0] == "MEDIUM_RISK_RULE":
        risk_score += 30

    # 🔵 ML contribution
    if "HIGH_RISK" in m[0]:
        risk_score += 35
    elif "MEDIUM_RISK" in m[0]:
        risk_score += 20

    # 🟢 Velocity contribution
    if v[0] == "CRITICAL":
        risk_score += 40
    elif v[0] == "SUSPICIOUS":
        risk_score += 25

    # 🟡 Pattern contribution
    if p[0] == "SUSPICIOUS":
        risk_score += 20
    elif p[0] == "WATCHLIST":
        risk_score += 10

    # 🎯 FINAL DECISION LOGIC
    if risk_score >= 80:
        decision = "BLOCK & FREEZE"
    elif risk_score >= 50:
        decision = "HOLD + MANUAL REVIEW"
    elif risk_score >= 25:
        decision = "STEP-UP AUTHENTICATION"
    else:
        decision = "ALLOW"

    return risk_score, decision, priority_flags


# =========================
# 🧠 EXPLAINABILITY ENGINE
# =========================
def explain(txn, v, p, m, r):

    trace = []

    trace.append(f"ML Score: {txn['ml_score']:.2f}")
    trace.append(f"Velocity: {txn['velocity_7d']} txns/7d")
    trace.append(f"Deviation: {txn['amount_deviation']:.2f}x baseline")

    if v[0] == "CRITICAL":
        trace.append("Velocity Agent flagged extreme activity")

    if p[0] == "SUSPICIOUS":
        trace.append("Pattern Agent detected behavioral anomaly")

    if "HIGH_RISK" in m[0]:
        trace.append("ML Agent indicates high fraud probability")

    if r[0] == "HIGH_RISK_RULE":
        trace.append("RBI Agent triggered EWS rule (critical)")

    return trace


# =========================
# 🎛 STREAMLIT UI CONFIG
# =========================
st.set_page_config(page_title="Fraud Control Tower", layout="wide")

st.title("🏦 Agentic Fraud Control Tower")
st.caption("Multi-Agent Real-Time Fraud Detection System (No RAG Version)")


# =========================
# 🧠 SESSION MEMORY
# =========================
if "memory" not in st.session_state:
    st.session_state.memory = []


# =========================
# 🔄 LIVE TRANSACTION GENERATOR
# =========================
txn = {
    "amount": random.randint(1000, 20000),
    "velocity_7d": random.randint(1, 60),
    "amount_deviation": random.uniform(0.5, 5),
    "ml_score": random.random(),
    "flags": random.choices(
        ["VELOCITY_SPIKE", "FAILED_TXN", "NONE"], k=1
    )
}


# =========================
# 📊 DISPLAY TRANSACTION
# =========================
st.subheader("🔄 Live Transaction Feed")
st.json(txn)


# =========================
# 🧠 RUN AGENTS
# =========================
v = velocity_agent(txn)
p = pattern_agent(txn)
m = ml_agent(txn)
r = rbi_agent(txn)

risk_score, decision, priority = orchestrator(v, p, m, r)
trace = explain(txn, v, p, m, r)


# =========================
# 🧠 AGENT OUTPUTS PANEL
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧠 Agent Outputs")
    st.write("Velocity Agent:", v)
    st.write("Pattern Agent:", p)
    st.write("ML Agent:", m)
    st.write("RBI Agent:", r)

with col2:
    st.subheader("🚨 Decision Engine")
    st.metric("Risk Score", risk_score)

    if decision == "ALLOW":
        st.success(decision)
    elif "STEP-UP" in decision:
        st.warning(decision)
    else:
        st.error(decision)


# =========================
# 🧠 EXPLAINABILITY TRACE
# =========================
st.subheader("🧠 Decision Reasoning Trace")

for t in trace:
    st.write("•", t)


# =========================
# 🚨 CASE MANAGEMENT SYSTEM
# =========================
if decision != "ALLOW":

    case_id = str(uuid.uuid4())

    st.subheader("🚨 FRAUD CASE GENERATED")
    st.write("Case ID:", case_id)
    st.write("Status: OPEN")
    st.write("Assigned Team: Fraud Ops / AML Team")

    st.session_state.memory.append({
        "case_id": case_id,
        "amount": txn["amount"],
        "risk_score": risk_score,
        "decision": decision
    })


# =========================
# 🧠 MEMORY DASHBOARD
# =========================
st.subheader("🧠 Fraud Case Memory (Recent)")

st.json(st.session_state.memory[-5:])


# =========================
# 🔁 LIVE REFRESH
# =========================
time.sleep(2)
st.rerun()
