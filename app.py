import streamlit as st
import random
import uuid
import time

# =========================
# 🧠 INIT STATE
# =========================
if "cases" not in st.session_state:
    st.session_state.cases = []

if "human_queue" not in st.session_state:
    st.session_state.human_queue = []

if "weights" not in st.session_state:
    st.session_state.weights = {
        "velocity": 1.0,
        "pattern": 1.0,
        "ml": 1.0,
        "rbi": 1.0
    }


# =========================
# 🧠 UTIL: CAP WEIGHTS (IMPORTANT)
# =========================
def cap_weights(weights):
    for k in weights:
        weights[k] = max(0.5, min(weights[k], 2.0))
    return weights


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
# 🟣 RBI AGENT
# =========================
def rbi_agent(txn):
    if "VELOCITY_SPIKE" in txn["flags"] and txn["amount"] > 12000:
        return "HIGH_RISK_RULE", "EWS: velocity + high amount"
    elif "FAILED_TXN" in txn["flags"]:
        return "MEDIUM_RISK_RULE", "EWS: failed transactions"
    else:
        return "CLEAR", "No rule triggered"


# =========================
# 🧠 ORCHESTRATOR (DECISION ENGINE)
# =========================
def orchestrator(v, p, m, r, weights):

    score = 0
    rbi_override = False

    # 🟣 RBI override (highest priority)
    if r[0] == "HIGH_RISK_RULE":
        return 100, "BLOCK & FREEZE", True

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

    # normalize risk score
    score = min(100, max(0, score))

    # 🧠 DECISION WITH HUMAN-IN-THE-LOOP
    if score >= 80:
        decision = "BLOCK & FREEZE"
    elif score >= 60:
        decision = "HUMAN REVIEW (HITL)"
    elif score >= 40:
        decision = "STEP-UP AUTH (OTP)"
    else:
        decision = "ALLOW"

    return score, decision, rbi_override


# =========================
# 📊 EXPLAINABILITY (STABLE SHAP-LIKE)
# =========================
def explain(txn):

    total = txn["amount"] + txn["velocity_7d"] + (txn["amount_deviation"] * 100) + (txn["ml_score"] * 100)

    return {
        "amount_impact": txn["amount"] / total,
        "velocity_impact": txn["velocity_7d"] / total,
        "deviation_impact": (txn["amount_deviation"] * 100) / total,
        "ml_impact": txn["ml_score"]
    }


# =========================
# 🔁 LEARNING LOOP (CONTROLLED)
# =========================
def learning_loop(decision, weights):

    if decision == "BLOCK & FREEZE":
        weights["velocity"] += 0.01
        weights["ml"] += 0.01
        weights["rbi"] += 0.01

    elif decision == "ALLOW":
        weights["ml"] -= 0.005

    return cap_weights(weights)


# =========================
# 🎛 STREAMLIT UI
# =========================
st.set_page_config(page_title="Fraud SOC", layout="wide")

st.title("🏦 Fraud SOC Control Tower (Agentic + HITL + Learning)")
st.caption("Production-style Fraud Decision System (Explainable + Human-in-loop)")


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

st.subheader("🔄 Live Transaction Feed")
st.json(txn)


# =========================
# 🧠 RUN AGENTS
# =========================
v = velocity_agent(txn)
p = pattern_agent(txn)
m = ml_agent(txn)
r = rbi_agent(txn)

score, decision, _ = orchestrator(v, p, m, r, st.session_state.weights)

shap_vals = explain(txn)


# =========================
# 🧠 OUTPUT PANEL
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
    st.metric("Risk Score", score)

    if decision == "ALLOW":
        st.success(decision)
    elif "STEP-UP" in decision:
        st.warning(decision)
    elif "HUMAN" in decision:
        st.info(decision)
    else:
        st.error(decision)


# =========================
# 📊 EXPLAINABILITY
# =========================
st.subheader("📊 Explainability Layer")

for k, v in shap_vals.items():
    st.write(f"{k}: {v:.3f}")


# =========================
# 🚨 CASE MANAGEMENT
# =========================
if decision != "ALLOW":

    case_id = str(uuid.uuid4())

    case = {
        "case_id": case_id,
        "amount": txn["amount"],
        "risk_score": score,
        "decision": decision
    }

    st.session_state.cases.append(case)

    # 🧑 HUMAN LOOP QUEUE
    if "HUMAN" in decision:
        st.session_state.human_queue.append(case)

    st.subheader("🚨 Case Generated")
    st.write(case)


# =========================
# 🧑 HUMAN-IN-THE-LOOP QUEUE
# =========================
st.subheader("🧑 Human Review Queue")

if st.session_state.human_queue:
    st.json(st.session_state.human_queue[-5:])
else:
    st.info("No cases waiting for human review")


# =========================
# 🧠 CASE MEMORY
# =========================
st.subheader("🧠 Case Memory (Recent)")
st.json(st.session_state.cases[-5:])


# =========================
# 🔁 LEARNING UPDATE
# =========================
st.session_state.weights = learning_loop(decision, st.session_state.weights)

st.subheader("🧠 Adaptive Learning Weights")
st.json(st.session_state.weights)


# =========================
# 🔁 AUTO REFRESH
# =========================
time.sleep(2)
st.rerun()
