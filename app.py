import streamlit as st
import random
import uuid
import time

# =========================
# 🟢 SESSION STATE INIT
# =========================
if "memory" not in st.session_state:
    st.session_state.memory = []

if "weights" not in st.session_state:
    st.session_state.weights = {
        "velocity": 1.0,
        "pattern": 1.0,
        "ml": 1.0,
        "rbi": 1.0
    }

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
        return "WATCHLIST", f"Moderate deviation: {dev:.2f}x"
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
        return "MEDIUM_RISK", f"Risk: {score:.2f}"
    else:
        return "LOW_RISK", f"Low risk: {score:.2f}"


# =========================
# 🟣 RBI RULE AGENT
# =========================
def rbi_agent(txn):
    flags = txn["flags"]

    if "VELOCITY_SPIKE" in flags and txn["amount"] > 10000:
        return "HIGH_RISK_RULE", "RBI EWS: velocity + high value txn"
    elif "FAILED_TXN" in flags:
        return "MEDIUM_RISK_RULE", "RBI EWS: failed transactions"
    else:
        return "CLEAR", "No RBI violation"


# =========================
# 🧠 META ORCHESTRATOR (CONFLICT-AWARE)
# =========================
def orchestrator(v, p, m, r, weights):

    risk_score = 0
    priority_override = False

    # 🟣 RBI OVERRIDE (highest priority)
    if r[0] == "HIGH_RISK_RULE":
        risk_score += 60 * weights["rbi"]
        priority_override = True
    elif r[0] == "MEDIUM_RISK_RULE":
        risk_score += 30 * weights["rbi"]

    # 🔵 ML contribution
    if "HIGH_RISK" in m[0]:
        risk_score += 35 * weights["ml"]
    elif "MEDIUM_RISK" in m[0]:
        risk_score += 20 * weights["ml"]

    # 🟢 Velocity contribution
    if v[0] == "CRITICAL":
        risk_score += 40 * weights["velocity"]
    elif v[0] == "SUSPICIOUS":
        risk_score += 25 * weights["velocity"]

    # 🟡 Pattern contribution
    if p[0] == "SUSPICIOUS":
        risk_score += 20 * weights["pattern"]
    elif p[0] == "WATCHLIST":
        risk_score += 10 * weights["pattern"]

    # 🎯 FINAL DECISION
    if priority_override:
        decision = "BLOCK & FREEZE"

    elif risk_score >= 80:
        decision = "BLOCK & FREEZE"
    elif risk_score >= 50:
        decision = "HOLD + MANUAL REVIEW"
    elif risk_score >= 25:
        decision = "STEP-UP AUTHENTICATION"
    else:
        decision = "ALLOW"

    return risk_score, decision


# =========================
# 🧠 EXPLAINABILITY (SHAP-LIKE)
# =========================
def shap_explain(txn):

    return {
        "amount": random.uniform(-0.1, 0.3),
        "velocity_7d": random.uniform(0.1, 0.5),
        "amount_deviation": random.uniform(0.05, 0.4),
        "ml_score": random.uniform(0.2, 0.6)
    }


# =========================
# 🔁 LEARNING LOOP
# =========================
def learning_loop(decision, weights):

    if decision == "BLOCK & FREEZE":
        weights["velocity"] += 0.03
        weights["ml"] += 0.05
        weights["rbi"] += 0.04

    elif decision == "ALLOW":
        weights["ml"] -= 0.01

    return weights


# =========================
# 🎛 STREAMLIT UI
# =========================
st.set_page_config(page_title="Fraud Control Tower", layout="wide")

st.title("🏦 Agentic Fraud Control Tower")
st.caption("Multi-Agent + SHAP + Self-Learning Fraud Intelligence System")


# =========================
# 🔄 LIVE TRANSACTION
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

st.subheader("🔄 Live Transaction Feed")
st.json(txn)


# =========================
# 🧠 RUN AGENTS
# =========================
v = velocity_agent(txn)
p = pattern_agent(txn)
m = ml_agent(txn)
r = rbi_agent(txn)

risk_score, decision = orchestrator(v, p, m, r, st.session_state.weights)

shap_values = shap_explain(txn)


# =========================
# 🧠 AGENT OUTPUTS
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧠 Agent Outputs")
    st.write("Velocity:", v)
    st.write("Pattern:", p)
    st.write("ML:", m)
    st.write("RBI:", r)

with col2:
    st.subheader("🚨 Decision Engine")
    st.metric("Risk Score", round(risk_score, 2))

    if decision == "ALLOW":
        st.success(decision)
    elif "STEP-UP" in decision:
        st.warning(decision)
    else:
        st.error(decision)


# =========================
# 🧠 EXPLAINABILITY (SHAP)
# =========================
st.subheader("📊 SHAP Explainability (Simulated)")

for k, v in shap_values.items():
    st.write(f"{k}: impact → {v:.3f}")


# =========================
# 🚨 CASE MANAGEMENT
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
# 🔁 LEARNING LOOP UPDATE
# =========================
st.session_state.weights = learning_loop(decision, st.session_state.weights)

st.subheader("🧠 Learning Weights (Adaptive System)")
st.json(st.session_state.weights)


# =========================
# 🔁 AUTO REFRESH
# =========================
time.sleep(2)
st.rerun()
