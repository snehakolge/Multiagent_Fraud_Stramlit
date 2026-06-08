import streamlit as st
import pandas as pd
import numpy as np
import uuid
import time
import joblib
import shap

# =========================
# 🧠 LOAD MODEL
# =========================
# Replace with your trained model path
try:
    model = joblib.load("xgb_model.pkl")
except:
    model = None  # fallback safe mode


# =========================
# 🧠 SESSION STATE
# =========================
if "cases" not in st.session_state:
    st.session_state.cases = []

if "human_queue" not in st.session_state:
    st.session_state.human_queue = []

if "weights" not in st.session_state:
    st.session_state.weights = {
        "threshold": 0.5
    }


# =========================
# 🔄 SAMPLE TRANSACTION STREAM
# =========================
def generate_txn():
    return {
        "amount": np.random.randint(1000, 20000),
        "velocity_7d": np.random.randint(1, 60),
        "amount_deviation": np.random.uniform(0.5, 5),
        "failed_txn_flag": np.random.randint(0, 2)
    }


# =========================
# 🔵 FEATURE PREP
# =========================
def build_features(txn):
    return pd.DataFrame([[
        txn["amount"],
        txn["velocity_7d"],
        txn["amount_deviation"],
        txn["failed_txn_flag"]
    ]], columns=[
        "amount",
        "velocity_7d",
        "amount_deviation",
        "failed_txn_flag"
    ])


# =========================
# 🧠 ML PREDICTION
# =========================
def ml_score(txn):
    if model is None:
        return np.random.uniform(0, 1)  # fallback demo mode

    X = build_features(txn)
    return model.predict_proba(X)[0][1]


# =========================
# 📊 REAL SHAP EXPLAINER
# =========================
def explain(model, txn):

    X = build_features(txn)

    if model is None:
        return {
            "amount": 0.2,
            "velocity_7d": 0.3,
            "amount_deviation": 0.25,
            "failed_txn_flag": 0.25
        }

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    feature_names = X.columns

    explanation = {}
    for i, f in enumerate(feature_names):
        explanation[f] = float(abs(shap_values[0][i]))

    # normalize
    total = sum(explanation.values()) + 1e-6
    for k in explanation:
        explanation[k] /= total

    return explanation


# =========================
# 🟢 AGENTS
# =========================
def velocity_agent(txn):
    v = txn["velocity_7d"]
    if v > 45:
        return "CRITICAL", "Extreme velocity spike"
    elif v > 20:
        return "SUSPICIOUS", "High velocity"
    return "NORMAL", "Stable"


def pattern_agent(txn):
    d = txn["amount_deviation"]
    if d > 3:
        return "SUSPICIOUS", "Strong deviation"
    elif d > 1.5:
        return "WATCHLIST", "Moderate deviation"
    return "NORMAL", "Stable"


def rbi_agent(txn):
    if txn["failed_txn_flag"] == 1 and txn["amount"] > 10000:
        return "HIGH_RISK_RULE", "RBI EWS trigger"
    return "CLEAR", "No rule"


# =========================
# 🧠 DECISION ENGINE (CALIBRATED)
# =========================
def decision_engine(v, p, r, ml):

    score = 0

    # RBI override
    if r[0] == "HIGH_RISK_RULE":
        return 100, "BLOCK & FREEZE"

    if v[0] == "CRITICAL":
        score += 40
    elif v[0] == "SUSPICIOUS":
        score += 25

    if p[0] == "SUSPICIOUS":
        score += 25
    elif p[0] == "WATCHLIST":
        score += 10

    score += ml * 40

    score = min(100, max(0, score))

    # HITL logic (IMPORTANT)
    if score >= 80:
        decision = "BLOCK & FREEZE"
    elif score >= 60:
        decision = "HUMAN REVIEW"
    elif score >= 35:
        decision = "STEP-UP AUTH"
    else:
        decision = "ALLOW"

    return score, decision


# =========================
# 🔁 LEARNING LOOP (SAFE)
# =========================
def learning_loop(decision, threshold):

    if decision == "BLOCK & FREEZE":
        threshold += 0.01
    elif decision == "ALLOW":
        threshold -= 0.005

    return float(np.clip(threshold, 0.3, 0.8))


# =========================
# 🎛 UI
# =========================
st.set_page_config(page_title="Fraud SOC (Real ML)", layout="wide")

st.title("🏦 Fraud SOC Control Tower (REAL ML + SHAP + HITL)")
st.caption("Production-style Explainable Fraud Intelligence System")


# =========================
# 🔄 LIVE TXN
# =========================
txn = generate_txn()

st.subheader("🔄 Live Transaction")
st.json(txn)


# =========================
# 🧠 ML + AGENTS
# =========================
ml = ml_score(txn)

v = velocity_agent(txn)
p = pattern_agent(txn)
r = rbi_agent(txn)

score, decision = decision_engine(v, p, r, ml)


# =========================
# 📊 SHAP EXPLANATION
# =========================
explanation = explain(model, txn)


# =========================
# 📊 DASHBOARD
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🧠 Agents")
    st.write("Velocity:", v)
    st.write("Pattern:", p)
    st.write("RBI:", r)
    st.write("ML Score:", round(ml, 3))

with col2:
    st.subheader("🚨 Decision Engine")
    st.metric("Risk Score", round(score, 2))

    if decision == "ALLOW":
        st.success(decision)
    elif decision == "HUMAN REVIEW":
        st.warning(decision)
    else:
        st.error(decision)


# =========================
# 📊 SHAP PANEL
# =========================
st.subheader("📊 SHAP Explainability (Real Model)")

for k, v in explanation.items():
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

    if decision == "HUMAN REVIEW":
        st.session_state.human_queue.append(case)

    st.subheader("🚨 FRAUD CASE CREATED")
    st.json(case)


# =========================
# 🧑 HUMAN-IN-THE-LOOP
# =========================
st.subheader("🧑 Human Review Queue")

st.json(st.session_state.human_queue[-5:])


# =========================
# 🧠 CASE MEMORY
# =========================
st.subheader("🧠 Case Memory")

st.json(st.session_state.cases[-5:])


# =========================
# 🔁 LEARNING UPDATE
# =========================
st.session_state.weights["threshold"] = learning_loop(
    decision,
    st.session_state.weights["threshold"]
)

st.subheader("🧠 Learning State")
st.json(st.session_state.weights)


# =========================
# 🔁 REFRESH
# =========================
time.sleep(2)
st.rerun()
