import streamlit as st
import random
import uuid
import time

# =========================
# 🟢 AGENT 1: Velocity Agent
# =========================
def velocity_agent(txn):
    velocity = txn["velocity_7d"]

    if velocity > 40:
        return "CRITICAL", "Extreme transaction burst detected"
    elif velocity > 20:
        return "SUSPICIOUS", "Unusual spike in transaction frequency"
    else:
        return "NORMAL", "Velocity within normal range"


# =========================
# 🟡 AGENT 2: Pattern Agent
# =========================
def pattern_agent(txn):
    deviation = txn["amount_deviation"]

    if deviation > 3:
        return "SUSPICIOUS", "Amount significantly deviates from user behavior"
    elif deviation > 1.5:
        return "WATCHLIST", "Moderate deviation detected"
    else:
        return "NORMAL", "Spending pattern stable"


# =========================
# 🔵 AGENT 3: ML Agent
# =========================
def ml_agent(txn):
    score = txn["ml_score"]

    if score > 0.8:
        return "HIGH_RISK", score
    elif score > 0.4:
        return "MEDIUM_RISK", score
    else:
        return "LOW_RISK", score


# =========================
# 🟣 AGENT 4: RBI RULE AGENT
# =========================
def rbi_agent(txn):
    flags = txn["flags"]

    if "VELOCITY_SPIKE" in flags and txn["amount"] > 10000:
        return "HIGH_RISK_RULE", "RBI EWS: velocity + high value transaction"
    elif "FAILED_TXN" in flags:
        return "MEDIUM_RISK_RULE", "Multiple failed attempts detected"
    else:
        return "CLEAR", "No regulatory violation detected"


# =========================
# 🧠 ORCHESTRATOR (BRAIN)
# =========================
def orchestrator(v, p, m, r):

    risk_score = 0

    # Velocity contribution
    if v[0] == "CRITICAL":
        risk_score += 40
    elif v[0] == "SUSPICIOUS":
        risk_score += 25

    # Pattern contribution
    if p[0] == "SUSPICIOUS":
        risk_score += 20
    elif p[0] == "WATCHLIST":
        risk_score += 10

    # ML contribution
    if m[0] == "HIGH_RISK":
        risk_score += 40
    elif m[0] == "MEDIUM_RISK":
        risk_score += 20

    # RBI rule contribution (highest weight)
    if r[0] == "HIGH_RISK_RULE":
        risk_score += 50
    elif r[0] == "MEDIUM_RISK_RULE":
        risk_score += 25

    # Decision logic
    if risk_score >= 80:
        decision = "BLOCK & FREEZE"
    elif risk_score >= 50:
        decision = "HOLD + MANUAL REVIEW"
    elif risk_score >= 25:
        decision = "STEP-UP AUTHENTICATION"
    else:
        decision = "ALLOW"

    return risk_score, decision


# =========================
# 🧠 EXPLAINABILITY LAYER
# =========================
def explain_decision(txn, v, p, m, r):

    explanation = []

    if v[0] == "CRITICAL":
        explanation.append(f"Velocity spike: {txn['velocity_7d']} transactions in 7 days")

    if p[0] == "SUSPICIOUS":
        explanation.append(f"Behavior deviation: {txn['amount_deviation']:.2f}x baseline")

    if m[0] == "HIGH_RISK":
        explanation.append(f"ML fraud probability: {txn['ml_score']:.2f}")

    if r[0] == "HIGH_RISK_RULE":
        explanation.append("RBI EWS rule triggered: velocity + high-value pattern")

    return explanation


# =========================
# 🎛 STREAMLIT UI
# =========================
st.set_page_config(page_title="Fraud Control Tower", layout="wide")

st.title("🏦 Agentic Fraud Control Tower")
st.write("Real-time Multi-Agent Fraud Detection System (Prototype)")

# =========================
# 🔄 SESSION MEMORY
# =========================
if "fraud_memory" not in st.session_state:
    st.session_state.fraud_memory = []


# =========================
# 🔄 LIVE TRANSACTION SIMULATION
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

risk_score, decision = orchestrator(v, p, m, r)
explanations = explain_decision(txn, v, p, m, r)


# =========================
# 🧠 AGENT OUTPUTS
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
for e in explanations:
    st.write("•", e)


# =========================
# 🚨 CASE MANAGEMENT SYSTEM
# =========================
if decision != "ALLOW":

    case_id = str(uuid.uuid4())

    st.subheader("🚨 FRAUD CASE GENERATED")
    st.write("Case ID:", case_id)
    st.write("Status: OPEN")
    st.write("Assigned Team: Fraud Ops / AML Team")

    st.session_state.fraud_memory.append({
        "case_id": case_id,
        "amount": txn["amount"],
        "risk": risk_score,
        "decision": decision
    })


# =========================
# 🧠 MEMORY (LAST CASES)
# =========================
st.subheader("🧠 Fraud Case Memory (Recent)")
st.json(st.session_state.fraud_memory[-5:])


# =========================
# 🔁 AUTO REFRESH (LIVE SIMULATION)
# =========================
time.sleep(2)
st.rerun()
