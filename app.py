from sklearn.pipeline import Pipeline
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import random
import time

from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(

    page_title="Enterprise Fraud Intelligence System",

    layout="wide"
)

st.title(
    "🏦 Enterprise Fraud Intelligence System"
)

st.markdown(
    "LangGraph Multi-Agent AI Fraud Detection Platform"
)

# =====================================================
# LOAD MODEL
# =====================================================

try:
    model = joblib.load("fraud_model.pkl")
    feature_columns = joblib.load("feature_columns.pkl")
except FileNotFoundError:
    st.error("Model files (fraud_model.pkl, feature_columns.pkl) not found. Please run the AutoML agent first to train and save the model.")
    st.stop()

# =====================================================
# SYNTHETIC TRANSACTION GENERATOR
# =====================================================

def generate_transaction():

    return {

        "amount":
        random.randint(100, 200000),

        "transaction_velocity_7d":
        random.randint(1, 50),

        "avg_amount_30d":
        random.randint(100, 100000),

        "amount_deviation_ratio":
        random.uniform(0.1, 10),

        "shared_device_count":
        random.randint(0, 10),

        "hour":
        random.randint(0, 23),

        "is_night":
        random.randint(0, 1),

        "merchant_ring_id":
        random.randint(0, 5),

        "customer_merchant_txn_count":
        random.randint(1, 20)
    }

# =====================================================
# LANGGRAPH STATE
# =====================================================

class FraudState(TypedDict):

    dataset: pd.DataFrame

    fraud_probability: float

    alert: str

    explanation: dict

    critical_action: bool

# =====================================================
# FEATURE AGENT
# =====================================================

def feature_agent(state):

    print("Feature Agent Running")

    return state

# =====================================================
# FRAUD AGENT
# =====================================================

def fraud_agent(state):

    print("Fraud Agent Running")

    df = state["dataset"]

    # COLUMN ALIGNMENT
    # This assumes `feature_columns` are the columns the model was trained on.
    if not isinstance(model, Pipeline) and hasattr(model, 'feature_names_in_'):
        # For models like XGBoost that store feature_names_in_
        aligned_df = df.reindex(columns=model.feature_names_in_, fill_value=0)
    elif feature_columns is not None and len(feature_columns) > 0:
        aligned_df = df.reindex(columns=feature_columns, fill_value=0)
    else:
        st.error("Cannot align columns: `feature_columns` not loaded or model has no `feature_names_in_`.")
        st.stop()

    fraud_prob = model.predict_proba(
        aligned_df
    )[0][1]

    state["fraud_probability"] = float(
        fraud_prob
    )

    return state

# =====================================================
# SHAP AGENT
# =====================================================

def shap_agent(state):

    print("SHAP Agent Running")

    df = state["dataset"]

    # COLUMN ALIGNMENT
    if not isinstance(model, Pipeline) and hasattr(model, 'feature_names_in_'):
        aligned_df = df.reindex(columns=model.feature_names_in_, fill_value=0)
    elif feature_columns is not None and len(feature_columns) > 0:
        aligned_df = df.reindex(columns=feature_columns, fill_value=0)
    else:
        st.error("Cannot align columns for SHAP: `feature_columns` not loaded or model has no `feature_names_in_`.")
        state["explanation"] = {}
        return state

    try:
        # Ensure SHAP can handle the model type
        if hasattr(model, 'predict_proba'): # Classifier
            explainer = shap.Explainer(model.predict_proba, aligned_df)
        elif hasattr(model, 'predict'): # Other types of models
            explainer = shap.Explainer(model.predict, aligned_df)
        else:
            st.warning("SHAP explainer cannot be created for this model type.")
            state["explanation"] = {}
            return state

        shap_values = explainer(aligned_df)

        feature_scores = {}

        # Depending on SHAP explainer, shap_values.values might be 2D for multi-output or 1D.
        # Assume single output for this fraud detection.
        if hasattr(shap_values, 'values') and len(shap_values.values.shape) > 1:
            # For classification, we usually look at the SHAP values for the positive class (index 1)
            shap_values_for_positive_class = shap_values.values[0, :, 1] if shap_values.values.ndim == 3 else shap_values.values[0]
            for i, col in enumerate(aligned_df.columns):
                feature_scores[col] = abs(shap_values_for_positive_class[i])
        elif hasattr(shap_values, 'values'): # Single output model
             for i, col in enumerate(aligned_df.columns):
                feature_scores[col] = abs(shap_values.values[0][i])
        else:
            st.warning("SHAP values structure not as expected.")
            state["explanation"] = {}
            return state

        top_features = dict(

            sorted(

                feature_scores.items(),

                key=lambda item: item[1],

                reverse=True

            )[:5]
        )

        state["explanation"] = top_features

    except Exception as e:

        st.error(f"Error generating SHAP explanation: {e}")
        state["explanation"] = {}

    return state

# =====================================================
# ROUTING FUNCTION
# =====================================================

def route_risk(state):

    if state["fraud_probability"] > 0.90:

        return "critical_alert_agent"

    return "monitoring_agent"

# =====================================================
# CRITICAL ALERT AGENT
# =====================================================

def critical_alert_agent(state):

    print("Critical Alert Agent Running")

    state["critical_action"] = True

    return state

# =====================================================
# MONITORING AGENT
# =====================================================

def monitoring_agent(state):

    print("Monitoring Agent Running")

    state["critical_action"] = False

    return state

# =====================================================
# ALERT AGENT
# =====================================================

def alert_agent(state):

    prob = state["fraud_probability"]

    if prob > 0.90:

        alert = "CRITICAL FRAUD ALERT"

    elif prob > 0.70:

        alert = "HIGH RISK ALERT"

    elif prob > 0.50:

        alert = "SUSPICIOUS TRANSACTION"

    else:

        alert = "GENUINE TRANSACTION"

    state["alert"] = alert

    return state

# =====================================================
# BUILD LANGGRAPH
# =====================================================

workflow = StateGraph(FraudState)

workflow.add_node(
    "feature_agent",
    feature_agent
)

workflow.add_node(
    "fraud_agent",
    fraud_agent
)

workflow.add_node(
    "shap_agent",
    shap_agent
)

workflow.add_node(
    "critical_alert_agent",
    critical_alert_agent
)

workflow.add_node(
    "monitoring_agent",
    monitoring_agent
)

workflow.add_node(
    "alert_agent",
    alert_agent
)

workflow.set_entry_point(
    "feature_agent"
)

workflow.add_edge(
    "feature_agent",
    "fraud_agent"
)

workflow.add_edge(
    "fraud_agent",
    "shap_agent"
)

workflow.add_conditional_edges(

    "shap_agent",

    route_risk,

    {

        "critical_alert_agent":
        "critical_alert_agent",

        "monitoring_agent":
        "monitoring_agent"
    }
)

workflow.add_edge(
    "critical_alert_agent",
    "alert_agent"
)

workflow.add_edge(
    "monitoring_agent",
    "alert_agent"
)

workflow.add_edge(
    "alert_agent",
    END
)

app = workflow.compile()

# =====================================================
# REAL-TIME MONITORING
# =====================================================

st.subheader(
    "🚨 Real-Time Fraud Monitoring"
)

start_button = st.button(
    "Start Monitoring"
)

if start_button:

    placeholder = st.empty()

    for i in range(20):

        txn = generate_transaction()

        txn_df = pd.DataFrame([txn])

        initial_state = {

            "dataset": txn_df,

            "fraud_probability": 0,

            "alert": "",

            "explanation": {},

            "critical_action": False
        }

        result = app.invoke(
            initial_state
        )

        with placeholder.container():

            st.write("---")

            st.write(
                f"## Transaction #{i+1}"
            )

            st.dataframe(txn_df)

            st.write(
                f"### Fraud Probability: "
                f"{round(result['fraud_probability'],4)}"
            )

            st.write(
                f"### Alert: "
                f"{result['alert']}"
            )

            st.write(
                f"### Critical Action: "
                f"{result['critical_action']}"
            )

            st.write(
                "### SHAP Fraud Drivers"
            )

            if len(result["explanation"]) > 0:

                shap_df = pd.DataFrame({

                    "Feature":
                    result["explanation"].keys(),

                    "Importance":
                    result["explanation"].values()

                })

                st.dataframe(shap_df)

            else:

                st.warning(
                    "No SHAP explanation generated"
                )

        time.sleep(2)

