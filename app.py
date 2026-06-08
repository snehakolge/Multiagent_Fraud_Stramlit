import streamlit as st
import random
import uuid
import time

# =========================
# 🧠 INIT SESSION STATE
# =========================
if "cases" not in st.session_state:
    st.session_state.cases = []

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

    if v > 45:
        return "CRITICAL", f"Extreme burst: {v}/7d"
    elif v > 20:
        return "SUSPICIOUS", f"High velocity: {v}/7d"
    else:
        return "NORMAL", f"Normal: {v}/7d"


# =========================
# 🟡 PATTERN AGENT
# =========================
def pattern_agent(txn):
    d = txn["amount_deviation"]

    if d > 3:
        return "SUSPICIOUS", f"Deviation: {d:.2f}x"
    elif d > 1.5:
        return "WATCHLIST", f"Moderate deviation: {d:.2f}x"
    else:
        return "NORMAL", f"Stable: {d:.2f}x"


# =========================
# 🔵 ML AGENT
# =========================
def ml_agent(txn):
    score = txn["ml_score"]

    if score > 0.8:
        return "HIGH_RISK", f"Score: {score:.2f}"
    elif score > 0.4:
        return "MEDIUM_RISK", f"Score: {score:.2f}"
    else:
        return "LOW_RISK", f"Score: {score:.2f}"


# =========================
# 🟣 RBI RULE AGENT
# =========================
def rbi_agent(txn):
    if "VELOCITY_SPIKE" in txn["flags"] and txn["amount"] > 12000:
        return "HIGH_RISK_RULE", "EWS: velocity + high amount"
    elif "FAILED_TXN" in txn["flags"]:
        return "MEDIUM_RISK_RULE", "EWS: failed transactions"
    else:
        return "CLEAR", "No rule triggered"


# =========================
# 🧠 ORCHESTRATOR (DECISION BRAIN)
# =========================
def orchestrator(v, p, m, r, weights):

    score = 0

    # 🟣 RBI OVERRIDE (highest priority)
    if r[0] == "HIGH_RISK_RULE":
        return 100, "BLOCK & FREEZE"

    # weighted scoring
    if v[0] == "CRITICAL":
        score += 40 * weights["velocity"]
    elif v[0] == "SUSPICIOUS":
        score += 25 * weights["velocity"]

    if p[0] == "SUSPICIOUS":
        score += 20 * weights["pattern"]
    elif p[0] == "WATCHLIST":
        score += 10 * weights["pattern"]

    if m[0] == "HIGH_RISK":
        score += 40 * weights["ml"]
    elif m[0] == "MEDIUM_RISK":
        score += 20 * weights["ml"]

    if r[0] == "MEDIUM_RISK_RULE":
        score += 25 * weights["rbi"]

    # decision
    if score >= 80:
        return score, "BLOCK & FREEZE"
    elif score >= 50:
        return score, "HOLD + MANUAL REVIEW"
    elif score >= 25:
        return score, "STEP-UP AUTH"
    else:
        return score, "ALLOW"


# =========================
# 📊 EXPLAINABILITY (SHAP-LIKE)
# =========================
def explain(txn):
    return {
        "amount_impact": random.uniform(0.1, 0.4),
        "velocity_impact": random.uniform(0.2, 0.6),
        "deviation_impact": random.uniform(0.1, 0.5),
        "ml_impact": random.uniform(0.3, 0.7)
    }


# =========================
# 🔁 LEARNING LOOP
# =========================
def learning_loop(decision, weights):

    if decision == "BLOCK & FREEZE":
        weights["velocity"] += 0.02
        weights["ml"] += 0.03
        weights["rbi"] += 0.02

    elif decision == "ALLOW":
        weights["ml"] -= 0.01

    return weights


# =========================
# 🎛 UI CONFIG
# =========================
st.set_page_config(page_title="Fraud SOC", layout="wide")

st.title("🏦 Fraud SOC Control Tower (Agentic AI)")
st.caption("Multi-Agent + SHAP + Learning Loop + Real-Time Simulation")


# =========================
# 🔄 LIVE TRANSACTION
# =========================
txn = {
    "amount": random.randint(1000, 20000),
    "velocity_7d": random.randint(1, 60),
    "amount_deviation": random.uniform(0.5, 5),
    "ml_score": random.random(),
    "flags": random.choices(["VELOCITY_SPIKE", "FAILED_TXN", "NONE"], k=1)
}

st.subheader("🔄 Live Transaction")
st.json(txn)


# =========================
# 🧠 RUN AGENTS
# =========================
v = velocity_agent(txn)
p = pattern_agent(txn)
m = ml_agent(txn)
r = rbi_agent(txn)

score, decision = orchestrator(v, p, m, r, st.session_state.weights)

shap_vals = explain(txn)


# =========================
# 🧠 AGENT OUTPUTS
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧠 Agents")
    st.write("Velocity:", v)
    st.write("Pattern:", p)
    st.write("ML:", m)
    st.write("RBI:", r)

with col2:
    st.subheader("🚨 Decision Engine")
    st.metric("Risk Score", round(score, 2))

    if decision == "ALLOW":
        st.success(decision)
    elif "STEP-UP" in decision:
        st.warning(decision)
    else:
        st.error(decision)


# =========================
# 📊 EXPLAINABILITY
# =========================
st.subheader("📊 SHAP-Like Explainability")

for k, v in shap_vals.items():
    st.write(f"{k}: {v:.3f}")


# =========================
# 🚨 CASE MANAGEMENT
# =========================
if decision != "ALLOW":

    case_id = str(uuid.uuid4())

    st.subheader("🚨 FRAUD CASE GENERATED")
    st.write("Case ID:", case_id)
    st.write("Status: OPEN")
    st.write("Team: Fraud Ops / AML")

    st.session_state.cases.append({
        "case_id": case_id,
        "amount": txn["amount"],
        "risk": score,
        "decision": decision
    })


# =========================
# 🧠 MEMORY DASHBOARD
# =========================
st.subheader("🧠 Case Memory")
st.json(st.session_state.cases[-5:])


# =========================
# 🔁 LEARNING UPDATE
# =========================
st.session_state.weights = learning_loop(decision, st.session_state.weights)

st.subheader("🧠 Learning Weights")
st.json(st.session_state.weights)


# =========================
# 🔁 AUTO REFRESH
# =========================
time.sleep(2)
st.rerun()
