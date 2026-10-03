import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client
import pandas as pd

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY")

st.set_page_config(page_title="NEXIO24 - AI Ops Dashboard", layout="wide")

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=30)
def load_conversations(limit=1000):
    res = get_client().table("conversations").select("*").order("created_at", desc=True).limit(limit).execute()
    return pd.DataFrame(res.data or [])

@st.cache_data(ttl=30)
def load_token_usage(limit=5000):
    res = get_client().table("token_usage").select("*").order("created_at", desc=True).limit(limit).execute()
    return pd.DataFrame(res.data or [])

@st.cache_data(ttl=30)
def load_guardrails(limit=1000):
    res = get_client().table("guardrail_events").select("*").order("created_at", desc=True).limit(limit).execute()
    return pd.DataFrame(res.data or [])

@st.cache_data(ttl=15)
def load_alerts(limit=50):
    res = get_client().table("alerts").select("*").order("created_at", desc=True).limit(limit).execute()
    return pd.DataFrame(res.data or [])

def load_budget():
    res = get_client().table("budget_config").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else {}

# ---------- Sidebar: Config ----------
st.sidebar.title("Config")
budget = load_budget()
st.sidebar.metric("Daily Budget ($)", budget.get("daily_budget_usd", 0))
st.sidebar.metric("Monthly Budget ($)", budget.get("monthly_budget_usd", 0))
st.sidebar.metric("Max Escalation Rate", budget.get("max_escalation_rate", 0))
st.sidebar.metric("Min Avg Confidence", budget.get("min_avg_confidence", 0))

def write_alert(alert_type, severity, message, value, threshold):
    get_client().table("alerts").insert({
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "value": float(value),
        "threshold": float(threshold),
    }).execute()

if st.sidebar.button("Run Alert Checks"):
    conv_ = load_conversations()
    usage_ = load_token_usage()

    checks = []

    # Daily budget
    if not usage_.empty:
        usage_["created_at"] = pd.to_datetime(usage_["created_at"])
        today = datetime.now(timezone.utc).date()
        today_cost = float(usage_[usage_["created_at"].dt.date == today]["cost_usd"].sum())
        if today_cost > float(budget.get("daily_budget_usd", 5)):
            checks.append(("daily_budget", "critical",
                          f"Today cost ${today_cost:.4f} exceeds budget ${budget['daily_budget_usd']}",
                          today_cost, budget["daily_budget_usd"]))

    # Escalation rate
    if not conv_.empty and "intent" in conv_.columns:
        real = conv_[conv_["agent"] != "qa"]
        if len(real) > 0:
            esc = float((real["intent"] == "escalation").mean())
            if esc > float(budget.get("max_escalation_rate", 0.3)):
                checks.append(("escalation_rate", "warning",
                              f"Escalation rate {esc:.1%} exceeds max {budget['max_escalation_rate']}",
                              esc, budget["max_escalation_rate"]))

    # Avg confidence
    if not conv_.empty and "confidence" in conv_.columns:
        real = conv_[conv_["agent"] != "qa"]
        valid = real[real["confidence"].notna()]
        if len(valid) > 0:
            conf = float(valid["confidence"].mean())
            if conf < float(budget.get("min_avg_confidence", 0.6)):
                checks.append(("confidence_drop", "warning",
                              f"Avg confidence {conf:.2f} below min {budget['min_avg_confidence']}",
                              conf, budget["min_avg_confidence"]))

    if not checks:
        st.sidebar.success("All checks passed.")
    else:
        for c in checks:
            write_alert(*c)
        st.sidebar.warning(f"Wrote {len(checks)} alert(s).")

# Sidebar: recent unacknowledged alerts
try:
    recent_alerts = get_client().table("alerts").select("*").eq("acknowledged", False).order("created_at", desc=True).limit(5).execute().data
    if recent_alerts:
        st.sidebar.markdown("**Recent Alerts**")
        for a in recent_alerts:
            st.sidebar.caption(f"[{a['severity']}] {a['message']}")
except Exception:
    pass

# ---------- Header ----------
st.title("AI Ops Dashboard")
st.caption("Project 3 - Monitoring | Guardrails | Cost Control | Security")

conv = load_conversations()
usage = load_token_usage()
guard = load_guardrails()

# ---------- Sidebar: Filters ----------
st.sidebar.divider()
st.sidebar.subheader("Filters")

agent_options = ["All"] + sorted(conv["agent"].dropna().unique().tolist()) if not conv.empty and "agent" in conv.columns else ["All"]
selected_agent = st.sidebar.selectbox("Agent", agent_options)

model_options = ["All"] + sorted(usage["model"].dropna().unique().tolist()) if not usage.empty and "model" in usage.columns else ["All"]
selected_model = st.sidebar.selectbox("Model", model_options)

if selected_agent != "All" and not conv.empty:
    conv = conv[conv["agent"] == selected_agent]

if selected_model != "All" and not usage.empty:
    usage = usage[usage["model"] == selected_model]

# ---------- KPI Row ----------
total_conv = len(conv)
total_cost = float(usage["cost_usd"].sum()) if not usage.empty else 0.0
cost_per_conv = round(total_cost / total_conv, 4) if total_conv > 0 else 0.0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Conversations", total_conv)
c2.metric("LLM Calls", len(usage))
c3.metric("Total Tokens", int(usage["total_tokens"].sum()) if not usage.empty else 0)
c4.metric("Total Cost ($)", round(total_cost, 4))
c5.metric("Cost / Conv ($)", cost_per_conv)
c6.metric("Guardrail Events", len(guard))

st.divider()

# ---------- Cost over time ----------
st.subheader("Cost Over Time (Last 7 Days)")
if not usage.empty:
    usage["created_at"] = pd.to_datetime(usage["created_at"])
    daily = usage.set_index("created_at").resample("D")["cost_usd"].sum().reset_index()
    daily.columns = ["date", "cost_usd"]
    st.line_chart(daily.set_index("date"))
else:
    st.info("No token usage data.")

# ---------- Cost by Agent + Model ----------
col1, col2 = st.columns(2)
with col1:
    st.subheader("Cost by Agent")
    if not usage.empty:
        st.bar_chart(usage.groupby("agent")["cost_usd"].sum())
with col2:
    st.subheader("Tokens by Model")
    if not usage.empty:
        st.bar_chart(usage.groupby("model")["total_tokens"].sum())

st.divider()

# ---------- Guardrails ----------
col3, col4 = st.columns(2)
with col3:
    st.subheader("Guardrail Events by Type")
    if not guard.empty:
        st.bar_chart(guard["event_type"].value_counts())
with col4:
    st.subheader("Guardrail Events by Severity")
    if not guard.empty:
        st.bar_chart(guard["severity"].value_counts())

st.divider()

# ---------- Live Alert Checks ----------
st.subheader("Live Alert Checks")
today = datetime.now(timezone.utc).date()
today_cost = 0.0
if not usage.empty:
    today_cost = float(usage[usage["created_at"].dt.date == today]["cost_usd"].sum())

esc_rate = 0.0
if not conv.empty and "intent" in conv.columns:
    real = conv[conv["agent"] != "qa"]
    if len(real) > 0:
        esc_rate = float((real["intent"] == "escalation").mean())

avg_conf = 0.0
if not conv.empty and "confidence" in conv.columns:
    avg_conf = float(conv["confidence"].fillna(0).mean())

a1, a2, a3 = st.columns(3)
a1.metric("Today Cost ($)", round(today_cost, 4),
          delta=f"budget {budget.get('daily_budget_usd', 0)}",
          delta_color="inverse" if today_cost > float(budget.get("daily_budget_usd", 5)) else "normal")
a2.metric("Escalation Rate", f"{esc_rate:.1%}",
          delta=f"max {budget.get('max_escalation_rate', 0)}",
          delta_color="inverse" if esc_rate > float(budget.get("max_escalation_rate", 0.3)) else "normal")
a3.metric("Avg Confidence", round(avg_conf, 2),
          delta=f"min {budget.get('min_avg_confidence', 0)}",
          delta_color="inverse" if avg_conf < float(budget.get("min_avg_confidence", 0.6)) else "normal")

st.divider()

# ---------- Alert History ----------
st.subheader("Alert History")
alerts_df = load_alerts()
if alerts_df.empty:
    st.info("No alerts yet. Click 'Run Alert Checks' in the sidebar.")
else:
    unack = alerts_df[alerts_df["acknowledged"] == False]
    st.caption(f"{len(unack)} unacknowledged / {len(alerts_df)} total")

    for _, row in alerts_df.head(20).iterrows():
        sev = row["severity"]
        icon = "🔴" if sev == "critical" else ("🟡" if sev == "warning" else "🔵")
        cols = st.columns([0.06, 0.14, 0.5, 0.15, 0.15])
        cols[0].write(icon)
        cols[1].write(row["alert_type"])
        cols[2].write(row["message"])
        cols[3].write(f"{row['value']:.3f} / {row['threshold']:.3f}")
        if not row["acknowledged"]:
            if cols[4].button("Ack", key=f"ack_{row['id']}"):
                get_client().table("alerts").update({"acknowledged": True}).eq("id", int(row["id"])).execute()
                st.cache_data.clear()
                st.rerun()
        else:
            cols[4].caption("acked")

st.divider()

# ---------- Recent Tables ----------
st.subheader("Recent Conversations")
st.dataframe(conv.head(30), use_container_width=True)

st.subheader("Recent Guardrail Events")
if not guard.empty:
    st.dataframe(guard.head(30), use_container_width=True)

st.subheader("Recent Token Usage")
if not usage.empty:
    st.dataframe(usage.head(30), use_container_width=True)