import streamlit as st
import random
import uuid
import time

# ---------------------------
# 🟢 AGENT 1: Velocity Agent
# ---------------------------
def velocity_agent(txn):
    velocity = txn["velocity_7d"]

    if velocity > 40:
        return "CRITICAL", "Extreme transaction burst detected"
    elif velocity > 20:
        return "SUSPICIOUS", "Unusual spike in transaction frequency"
    else:
        return "NORMAL", "Velocity within normal range"


# ---------------------------
# 🟡 AGENT 2: Pattern Agent
# ---------------------------
def pattern_agent(txn):
    deviation = txn["amount_deviation"]

    if deviation > 3:
        return "SUSPICIOUS", "Amount significantly deviates from user behavior"
    elif deviation > 1.5:
        return "WATCHLIST", "Moderate deviation detected"
    else:
        return "NORMAL", "Spending pattern stable"


# ---------------------------
# 🔵 AGENT 3: ML MODEL AGENT
# ---------------------------
def ml_agent(txn):
    score = txn["ml_score"]

    if score > 0.8:
        return "HIGH_RISK", score
    elif score > 0.4:
        return "MEDIUM_RISK", score
    else:
        return "LOW_RISK", score


# ---------------------------
# 🟣 AGENT 4: RBI / RULE ENGINE
# ---------------------------
def rbi_agent(txn):
    flags = txn["flags"]

    if "VELOCITY_SPIKE" in flags and txn["amount"] > 10000:
        return "HIGH_RISK_RULE", "RBI EWS: velocity + high value transaction"
    elif "MANY_FAILED_TXNS" in flags:
        return "MEDIUM_RISK_RULE", "Multiple failed attempts detected"
    else:
        return "CLEAR", "No regulatory violation detected"


# ---------------------------
# 🧠 ORCHESTRATOR (Decision Brain)
# ---------------------------
def orchestrator(v, p, m, r):
    
    risk_score = 0
    reasons = []

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

    # RBI rules (VERY HIGH IMPACT)
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

    return risk_score, reasons, decision


# ---------------------------
# 🎛 STREAMLIT UI
# ---------------------------
st.title("🏦 Agentic Fraud Control Tower")

st.write("Real-time Multi-Agent Fraud Detection System")

# Simulated transaction
txn = {
    "amount": random.randint(1000, 20000),
    "velocity_7d": random.randint(1, 60),
    "amount_deviation": random.uniform(0.5, 5),
    "ml_score": random.random(),
    "flags": random.choices(
        ["VELOCITY_SPIKE", "NONE", "FAILED_TXN"], k=1
    )
}

st.subheader("🔄 Live Transaction")
st.json(txn)

# Run Agents
v = velocity_agent(txn)
p = pattern_agent(txn)
m = ml_agent(txn)
r = rbi_agent(txn)

# Orchestrator Decision
risk_score, reasons, decision = orchestrator(v, p, m, r)

# ---------------------------
# OUTPUT
# ---------------------------
st.subheader("🧠 Agent Outputs")

st.write("Velocity Agent:", v)
st.write("Pattern Agent:", p)
st.write("ML Agent:", m)
st.write("RBI Agent:", r)

st.subheader("🚨 Final Decision Engine")

st.metric("Risk Score", risk_score)
st.success(f"Decision: {decision}")

# ---------------------------
# CASE MANAGEMENT
# ---------------------------
if decision != "ALLOW":
    case_id = str(uuid.uuid4())

    st.error("🚨 FRAUD CASE GENERATED")
    st.write("Case ID:", case_id)
    st.write("Status: OPEN")
    st.write("Assigned Team: Fraud Ops / AML Team")

# Auto refresh simulation
time.sleep(2)
st.rerun()
