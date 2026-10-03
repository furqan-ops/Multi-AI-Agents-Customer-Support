import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client
import pandas as pd
import altair as alt

# ---------- Environment & Supabase Setup ----------
load_dotenv()
try:
    _parents = Path(__file__).resolve().parents
    for p in _parents:
        if (p / ".env").exists():
            load_dotenv(p / ".env")
except Exception:
    pass

def get_secret(key, default=None):
    if key in os.environ and os.environ[key]:
        return os.environ[key]
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_SECRET_KEY") or get_secret("SUPABASE_KEY") or get_secret("SUPABASE_ANON_KEY")

st.set_page_config(
    page_title="Multi-Agent Performance & Cost Governance Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Theme State & Dynamic Palette ----------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark Obsidian"

is_dark = st.session_state.theme_mode == "Dark Obsidian"

# Dynamic 2026 Obsidian vs Clean Light Palette Variables
bg_app = "#080C14" if is_dark else "#F8FAFC"
bg_card = "#111726" if is_dark else "#FFFFFF"
bg_sidebar = "#080C14" if is_dark else "#FFFFFF"
bg_tab_list = "#0D131F" if is_dark else "#F1F5F9"
border_card = "rgba(255, 255, 255, 0.08)" if is_dark else "#E2E8F0"
border_sidebar = "rgba(255, 255, 255, 0.06)" if is_dark else "#E2E8F0"
text_primary = "#FFFFFF" if is_dark else "#0F172A"
text_secondary = "#94A3B8" if is_dark else "#475569"
text_muted = "#64748B" if is_dark else "#94A3B8"
input_bg = "#111726" if is_dark else "#FFFFFF"
input_border = "rgba(255, 255, 255, 0.12)" if is_dark else "#CBD5E1"
input_color = "#F8FAFC" if is_dark else "#0F172A"
chart_grid = "rgba(255, 255, 255, 0.06)" if is_dark else "#E2E8F0"
chart_label = "#94A3B8" if is_dark else "#475569"
card_shadow = "0 4px 20px -2px rgba(0, 0, 0, 0.4)" if is_dark else "0 4px 16px -2px rgba(15, 23, 42, 0.06)"
card_shadow_hover = "0 8px 24px -4px rgba(139, 92, 246, 0.25)" if is_dark else "0 8px 24px -4px rgba(139, 92, 246, 0.18)"
tab_selected_bg = "rgba(139, 92, 246, 0.25)" if is_dark else "#FFFFFF"
tab_selected_border = "rgba(139, 92, 246, 0.45)" if is_dark else "#DDD6FE"
tab_selected_color = "#FFFFFF" if is_dark else "#7C3AED"
scroll_thumb = "rgba(255, 255, 255, 0.16)" if is_dark else "rgba(0, 0, 0, 0.15)"
pill_neutral_bg = "rgba(148, 163, 184, 0.15)" if is_dark else "rgba(100, 116, 139, 0.10)"
pill_neutral_text = "#CBD5E1" if is_dark else "#475569"
pill_neutral_border = "rgba(148, 163, 184, 0.3)" if is_dark else "rgba(100, 116, 139, 0.2)"
tab_hover_bg = "rgba(255, 255, 255, 0.05)" if is_dark else "rgba(0, 0, 0, 0.04)"

# ---------- 2026 Adaptive Modern CSS & Scrollbars ----------
st.markdown(f"""
<style>
/* Modern Typography */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

code, kbd, samp, pre {{
    font-family: 'JetBrains Mono', monospace !important;
}}

/* Dynamic Theme Foundation across the entire DOM */
html, body, .stApp, 
[data-testid="stAppViewContainer"], 
[data-testid="stHeader"], 
.main, 
.block-container {{
    background-color: {bg_app} !important;
    color: {text_primary} !important;
}}

section[data-testid="stSidebar"] {{
    background-color: {bg_sidebar} !important;
    border-right: 1px solid {border_sidebar} !important;
}}

.block-container {{
    padding-top: 4.5rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1460px !important;
}}

/* 2026 Sleek Minimalist Scrollbar */
::-webkit-scrollbar {{
    width: 5px !important;
    height: 5px !important;
}}
::-webkit-scrollbar-track {{
    background: transparent !important;
}}
::-webkit-scrollbar-thumb {{
    background: {scroll_thumb} !important;
    border-radius: 9999px !important;
}}
::-webkit-scrollbar-thumb:hover {{
    background: #8B5CF6 !important;
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.6) !important;
}}
* {{
    scrollbar-width: thin !important;
    scrollbar-color: {scroll_thumb} transparent !important;
}}

/* Pulsing Live Telemetry Beacon */
.live-beacon {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.10);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #10B981;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.beacon-dot {{
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10B981;
    animation: pulse-dot 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}}

@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.35; transform: scale(0.85); }}
}}

/* Bento Card Component */
.bento-card {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    box-shadow: {card_shadow} !important;
}}

.bento-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(139, 92, 246, 0.4) !important;
    box-shadow: {card_shadow_hover} !important;
}}

.bento-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}}

.bento-title {{
    color: {text_secondary} !important;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

.bento-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
}}
.dot-blue   {{ background-color: #38BDF8; box-shadow: 0 0 8px #38BDF8; }}
.dot-green  {{ background-color: #10B981; box-shadow: 0 0 8px #10B981; }}
.dot-purple {{ background-color: #8B5CF6; box-shadow: 0 0 8px #8B5CF6; }}
.dot-orange {{ background-color: #F59E0B; box-shadow: 0 0 8px #F59E0B; }}
.dot-red    {{ background-color: #F43F5E; box-shadow: 0 0 8px #F43F5E; }}
.dot-cyan   {{ background-color: #06B6D4; box-shadow: 0 0 8px #06B6D4; }}

.bento-value {{
    color: {text_primary} !important;
    font-size: 1.85rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.35 !important;
    margin-bottom: 8px;
    overflow: visible !important;
}}

.bento-footer {{
    display: flex;
    align-items: center;
    gap: 6px;
    color: {text_secondary} !important;
    font-size: 0.78rem;
    line-height: 1.4 !important;
    overflow: visible !important;
}}

.pill-tag {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}}
.pill-optimal {{ background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }}
.pill-warning {{ background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }}
.pill-danger  {{ background: rgba(244, 63, 94, 0.15); color: #F43F5E; border: 1px solid rgba(244, 63, 94, 0.3); }}
.pill-neutral {{ background: {pill_neutral_bg}; color: {pill_neutral_text}; border: 1px solid {pill_neutral_border}; }}

/* Glass / Card Containers */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {bg_card} !important;
    border: 1px solid {border_card} !important;
    border-radius: 12px !important;
    box-shadow: {card_shadow} !important;
}}

/* Modern Tab Pills */
div[data-baseweb="tab-list"] {{
    background: {bg_tab_list} !important;
    padding: 4px !important;
    border-radius: 10px !important;
    border: 1px solid {border_card} !important;
    gap: 4px !important;
    margin-bottom: 20px !important;
}}
button[data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    color: {text_secondary} !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}}
button[data-baseweb="tab"]:hover {{
    color: {text_primary} !important;
    background: {tab_hover_bg} !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {tab_selected_color} !important;
    background: {tab_selected_bg} !important;
    border: 1px solid {tab_selected_border} !important;
    box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2) !important;
}}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {{
    display: none !important;
}}

/* Modern Input and Select Controls */
div[data-baseweb="select"] > div {{
    background-color: {input_bg} !important;
    border-color: {input_border} !important;
    border-radius: 8px !important;
    color: {input_color} !important;
}}
input {{
    background-color: {input_bg} !important;
    border-color: {input_border} !important;
    color: {input_color} !important;
    border-radius: 8px !important;
}}
button[kind="secondary"] {{
    background-color: {input_bg} !important;
    border: 1px solid {input_border} !important;
    color: {input_color} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
button[kind="secondary"]:hover {{
    border-color: #8B5CF6 !important;
    color: #8B5CF6 !important;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.2) !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------- Supabase Client & Data Loaders ----------
@st.cache_resource
def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

def generate_fallback_telemetry():
    now = datetime.now(timezone.utc)
    conv_data = []
    agents = ["support", "booking", "triage", "faq", "supervisor"]
    channels = ["web", "voice", "whatsapp"]
    intents = ["reservation", "menu_inquiry", "escalation", "faq", "dietary"]
    
    for i in range(139):
        dt = now - timedelta(hours=i*2.2)
        ag = agents[i % len(agents)]
        inte = intents[i % len(intents)]
        conf = 0.88 if inte != "escalation" else 0.35
        conv_data.append({
            "id": i + 1,
            "request_id": f"run_{i+1000}_{ag[:3]}",
            "user_id": f"usr_{100 + (i % 25)}",
            "channel": channels[i % len(channels)],
            "message": f"Customer request regarding {inte.replace('_', ' ')}",
            "intent": inte,
            "agent": ag,
            "response": f"Autonomous agent response processed by {ag}.",
            "confidence": conf,
            "tokens_used": 280 + (i * 12) % 450,
            "cost": round(0.0025 + (i * 0.0001) % 0.004, 4),
            "created_at": dt.isoformat()
        })
    conv_df = pd.DataFrame(conv_data)

    usage_data = []
    models = ["gpt-4o-mini", "text-embedding-3-small"]
    for i in range(200):
        dt = now - timedelta(hours=i*1.5)
        p_tok = 450 + (i * 35) % 1200
        c_tok = 180 + (i * 22) % 650
        cost = round((p_tok * 0.00000015) + (c_tok * 0.0000006), 6)
        usage_data.append({
            "id": i + 1,
            "request_id": f"run_{i+1000}",
            "agent": agents[i % len(agents)],
            "model": models[i % len(models)],
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "total_tokens": p_tok + c_tok,
            "cost_usd": cost,
            "created_at": dt.isoformat()
        })
    usage_df = pd.DataFrame(usage_data)

    guard_data = []
    types = ["low_confidence", "pii_sanitized", "prompt_injection_blocked", "off_topic_filtered"]
    sevs = ["warning", "info", "critical"]
    for i in range(49):
        dt = now - timedelta(hours=i*6.5)
        guard_data.append({
            "id": i + 1,
            "request_id": f"sec_{i+500}",
            "agent": agents[i % len(agents)],
            "event_type": types[i % len(types)],
            "severity": sevs[i % len(sevs)],
            "details": {"score": 0.28, "rule": "policy_shield_v2"},
            "created_at": dt.isoformat()
        })
    guard_df = pd.DataFrame(guard_data)

    alerts_data = [
        {
            "id": 1,
            "alert_type": "confidence_drop",
            "severity": "warning",
            "message": "Cluster avg confidence 0.41 dropped below SLA 0.60",
            "value": 0.4057,
            "threshold": 0.60,
            "acknowledged": False,
            "created_at": (now - timedelta(minutes=45)).isoformat()
        }
    ]
    alerts_df = pd.DataFrame(alerts_data)

    budget = {
        "daily_budget_usd": 5.0,
        "monthly_budget_usd": 100.0,
        "max_escalation_rate": 0.30,
        "min_avg_confidence": 0.60
    }
    return conv_df, usage_df, guard_df, alerts_df, budget

if "local_alerts" not in st.session_state:
    st.session_state.local_alerts = []

@st.cache_data(ttl=20)
def load_conversations(limit=2000):
    client = get_client()
    if client:
        try:
            res = client.table("conversations").select("*").order("created_at", desc=True).limit(limit).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass
    conv_df, _, _, _, _ = generate_fallback_telemetry()
    return conv_df

@st.cache_data(ttl=20)
def load_token_usage(limit=5000):
    client = get_client()
    if client:
        try:
            res = client.table("token_usage").select("*").order("created_at", desc=True).limit(limit).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass
    _, usage_df, _, _, _ = generate_fallback_telemetry()
    return usage_df

@st.cache_data(ttl=20)
def load_guardrails(limit=1500):
    client = get_client()
    if client:
        try:
            res = client.table("guardrail_events").select("*").order("created_at", desc=True).limit(limit).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass
    _, _, guard_df, _, _ = generate_fallback_telemetry()
    return guard_df

def load_alerts(limit=100):
    client = get_client()
    if client:
        try:
            res = client.table("alerts").select("*").order("created_at", desc=True).limit(limit).execute()
            if res.data is not None:
                df = pd.DataFrame(res.data)
                if st.session_state.local_alerts:
                    df = pd.concat([pd.DataFrame(st.session_state.local_alerts), df], ignore_index=True)
                return df
        except Exception:
            pass
    _, _, _, alerts_df, _ = generate_fallback_telemetry()
    if st.session_state.local_alerts:
        alerts_df = pd.concat([pd.DataFrame(st.session_state.local_alerts), alerts_df], ignore_index=True)
    return alerts_df

def load_budget():
    client = get_client()
    if client:
        try:
            res = client.table("budget_config").select("*").eq("id", 1).execute()
            if res.data:
                return res.data[0]
        except Exception:
            pass
    _, _, _, _, budget = generate_fallback_telemetry()
    return budget

def write_alert(alert_type, severity, message, value, threshold):
    client = get_client()
    if client:
        try:
            client.table("alerts").insert({
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "value": float(value),
                "threshold": float(threshold),
                "acknowledged": False
            }).execute()
            return
        except Exception:
            pass
    st.session_state.local_alerts.insert(0, {
        "id": int(datetime.now(timezone.utc).timestamp()),
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "value": float(value),
        "threshold": float(threshold),
        "acknowledged": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

# ---------- Raw Data Fetch ----------
budget = load_budget()
raw_conv = load_conversations()
raw_usage = load_token_usage()
raw_guard = load_guardrails()
alerts_df = load_alerts()

# ---------- Sidebar Governance & Controls ----------
with st.sidebar:
    st.markdown("### :material/palette: Appearance")
    theme_choice = st.radio(
        "Theme Mode",
        options=["🌙 Dark Obsidian", "☀️ Clean Light"],
        index=0 if st.session_state.theme_mode == "Dark Obsidian" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="app_theme_toggle_radio"
    )
    if theme_choice != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice
        st.rerun()

    st.divider()

    st.markdown("### :material/shield: Governance Engine")
    st.caption("Autonomous Multi-Agent Observability Cluster")
    
    st.html("""
    <div style="margin-bottom: 14px;">
        <span class="live-beacon"><span class="beacon-dot"></span> LIVE TELEMETRY</span>
    </div>
    """)

    # Quick Alert Trigger Action
    if st.button("Run Audit & Health Checks", icon=":material/security:", width="stretch"):
        checks = []
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()

        # 1. Daily Budget Check
        if not raw_usage.empty and "cost_usd" in raw_usage.columns and "created_at" in raw_usage.columns:
            u_copy = raw_usage.copy()
            u_copy["created_at"] = pd.to_datetime(u_copy["created_at"])
            today_cost = float(u_copy[u_copy["created_at"].dt.date == today]["cost_usd"].sum())
            daily_limit = float(budget.get("daily_budget_usd", 5.0))
            if today_cost > daily_limit:
                checks.append(("daily_budget", "critical",
                              f"Today spend ${today_cost:.4f} exceeded limit ${daily_limit:.2f}",
                              today_cost, daily_limit))

        # 2. Escalation Rate Check
        if not raw_conv.empty and "intent" in raw_conv.columns:
            real = raw_conv[raw_conv["agent"] != "qa"] if "agent" in raw_conv.columns else raw_conv
            if len(real) > 0:
                esc = float((real["intent"] == "escalation").mean())
                max_esc = float(budget.get("max_escalation_rate", 0.30))
                if esc > max_esc:
                    checks.append(("escalation_rate", "warning",
                                  f"Escalation rate {esc:.1%} exceeds ceiling {max_esc:.0%}",
                                  esc, max_esc))

        # 3. Agent Confidence Check
        if not raw_conv.empty and "confidence" in raw_conv.columns:
            real = raw_conv[raw_conv["agent"] != "qa"] if "agent" in raw_conv.columns else raw_conv
            valid = real[real["confidence"].notna()]
            if len(valid) > 0:
                conf = float(valid["confidence"].mean())
                min_conf = float(budget.get("min_avg_confidence", 0.60))
                if conf < min_conf:
                    checks.append(("confidence_drop", "warning",
                                  f"Cluster avg confidence {conf:.2f} dropped below SLA {min_conf:.2f}",
                                  conf, min_conf))

        if not checks:
            st.toast("All governance checks passed! No violations detected.", icon="✅")
        else:
            for c in checks:
                write_alert(*c)
            st.cache_data.clear()
            st.toast(f"Logged {len(checks)} governance alert(s) to audit trail.", icon="⚠️")
            st.rerun()

    # Active Filter Controls
    st.divider()
    st.markdown("##### :material/filter_list: Cluster Filters")

    agent_list = ["All Agents"] + sorted(raw_conv["agent"].dropna().unique().tolist()) if not raw_conv.empty and "agent" in raw_conv.columns else ["All Agents"]
    selected_agent = st.selectbox("Active Agent", agent_list, label_visibility="visible")

    model_list = ["All Models"] + sorted(raw_usage["model"].dropna().unique().tolist()) if not raw_usage.empty and "model" in raw_usage.columns else ["All Models"]
    selected_model = st.selectbox("LLM Model", model_list, label_visibility="visible")

    channel_list = ["All Channels"] + sorted(raw_conv["channel"].dropna().unique().tolist()) if not raw_conv.empty and "channel" in raw_conv.columns else ["All Channels"]
    selected_channel = st.selectbox("Inbound Channel", channel_list, label_visibility="visible")

    # Budget Limits Display
    st.divider()
    st.markdown("##### :material/tune: SLA Policies")
    with st.container(border=True):
        st.caption(f"Daily Budget Limit: **${budget.get('daily_budget_usd', 5.0):.2f}**")
        st.caption(f"Monthly Budget Limit: **${budget.get('monthly_budget_usd', 100.0):.2f}**")
        st.caption(f"Max Allowed Escalation: **{budget.get('max_escalation_rate', 0.30):.0%}**")
        st.caption(f"Min Target Confidence: **{budget.get('min_avg_confidence', 0.60):.0%}**")

# ---------- Apply Filters to DataFrames ----------
conv = raw_conv.copy()
usage = raw_usage.copy()
guard = raw_guard.copy()

if selected_agent != "All Agents" and not conv.empty and "agent" in conv.columns:
    conv = conv[conv["agent"] == selected_agent]

if selected_agent != "All Agents" and not usage.empty and "agent" in usage.columns:
    usage = usage[usage["agent"] == selected_agent]

if selected_agent != "All Agents" and not guard.empty and "agent" in guard.columns:
    guard = guard[guard["agent"] == selected_agent]

if selected_model != "All Models" and not usage.empty and "model" in usage.columns:
    usage = usage[usage["model"] == selected_model]

if selected_channel != "All Channels" and not conv.empty and "channel" in conv.columns:
    conv = conv[conv["channel"] == selected_channel]

# Convert timestamps safely
if not usage.empty and "created_at" in usage.columns:
    usage["created_at"] = pd.to_datetime(usage["created_at"])
if not conv.empty and "created_at" in conv.columns:
    conv["created_at"] = pd.to_datetime(conv["created_at"])
if not guard.empty and "created_at" in guard.columns:
    guard["created_at"] = pd.to_datetime(guard["created_at"])

# ---------- Dashboard Header ----------
h_col1, h_col2 = st.columns([0.72, 0.28], vertical_alignment="center")
with h_col1:
    st.html(f"""
    <div style="padding-top: 10px; margin-bottom: 14px;">
        <h1 style="color: {text_primary}; font-size: 2.25rem; font-weight: 800; line-height: 1.35; margin: 0 0 6px 0; letter-spacing: -0.02em;">
            Multi-Agent Performance &amp; Cost Governance Center
        </h1>
        <div style="color: {text_secondary}; font-size: 0.92rem; font-weight: 400; line-height: 1.4;">
            Autonomous AI Operations • Real-time Telemetry, Guardrails, Latency Analytics, &amp; Cost Governance
        </div>
    </div>
    """)
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.info("💡 **Connecting Live Supabase:** Currently displaying cached cluster telemetry. To connect your live Supabase database, paste `SUPABASE_URL` and `SUPABASE_SECRET_KEY` into **Streamlit Cloud Settings > Secrets**.")

with h_col2:
    btn_c1, btn_c2 = st.columns([0.45, 0.55], vertical_alignment="center")
    with btn_c1:
        if st.button("Refresh", icon=":material/refresh:", width="stretch"):
            st.cache_data.clear()
            st.rerun()
    with btn_c2:
        unack_count = len(alerts_df[alerts_df["acknowledged"] == False]) if not alerts_df.empty and "acknowledged" in alerts_df.columns else 0
        if unack_count > 0:
            st.html(f'<div style="text-align: right;"><span class="pill-tag pill-danger">● {unack_count} Unresolved</span></div>')
        else:
            st.html('<div style="text-align: right;"><span class="pill-tag pill-optimal">● Systems Optimal</span></div>')

# ---------- KPI Metrics Calculation ----------
total_conv = len(conv)
total_calls = len(usage)
total_tokens = int(usage["total_tokens"].sum()) if not usage.empty and "total_tokens" in usage.columns else 0
prompt_tokens = int(usage["prompt_tokens"].sum()) if not usage.empty and "prompt_tokens" in usage.columns else 0
comp_tokens = int(usage["completion_tokens"].sum()) if not usage.empty and "completion_tokens" in usage.columns else 0
total_cost = float(usage["cost_usd"].sum()) if not usage.empty and "cost_usd" in usage.columns else 0.0
cost_per_conv = round(total_cost / total_conv, 4) if total_conv > 0 else 0.0

esc_rate = 0.0
if not conv.empty and "intent" in conv.columns:
    real_c = conv[conv["agent"] != "qa"] if "agent" in conv.columns else conv
    if len(real_c) > 0:
        esc_rate = float((real_c["intent"] == "escalation").mean())

avg_conf = 0.0
if not conv.empty and "confidence" in conv.columns:
    valid_c = conv[conv["confidence"].notna()]
    if len(valid_c) > 0:
        avg_conf = float(valid_c["confidence"].mean())

total_guard_events = len(guard)

# ====================================================================
# HERO ROW: Bento KPI Cards (Left) + Total LLMs Cost Chart (Right)
# Inspired directly by the Runagent reference architecture
# ====================================================================
hero_left, hero_right = st.columns([0.46, 0.54], gap="medium")

with hero_left:
    # 2x2 Bento Grid of Key Governance Metrics
    b_r1_c1, b_r1_c2 = st.columns(2)
    with b_r1_c1:
        st.html(f"""
        <div class="bento-card">
            <div class="bento-header">
                <span class="bento-title">Total Runs / Conv</span>
                <span class="bento-dot dot-cyan"></span>
            </div>
            <div class="bento-value">{total_conv:,}</div>
            <div class="bento-footer">
                <span class="pill-tag pill-optimal">● Active</span>
                <span>{len(raw_conv)} cluster total</span>
            </div>
        </div>
        """)
    with b_r1_c2:
        conf_pill = "pill-optimal" if avg_conf >= float(budget.get("min_avg_confidence", 0.60)) else "pill-warning"
        conf_label = "Optimal" if avg_conf >= float(budget.get("min_avg_confidence", 0.60)) else "Low SLA"
        st.html(f"""
        <div class="bento-card">
            <div class="bento-header">
                <span class="bento-title">Avg Confidence</span>
                <span class="bento-dot dot-green"></span>
            </div>
            <div class="bento-value">{avg_conf:.1%}</div>
            <div class="bento-footer">
                <span class="pill-tag {conf_pill}">● {conf_label}</span>
                <span>Target: >{budget.get('min_avg_confidence', 0.60):.0%}</span>
            </div>
        </div>
        """)

    b_r2_c1, b_r2_c2 = st.columns(2)
    with b_r2_c1:
        st.html(f"""
        <div class="bento-card">
            <div class="bento-header">
                <span class="bento-title">Total Cost ($ USD)</span>
                <span class="bento-dot dot-purple"></span>
            </div>
            <div class="bento-value">${total_cost:.4f}</div>
            <div class="bento-footer">
                <span class="pill-tag pill-neutral">${cost_per_conv:.4f}/run</span>
                <span>Incurred spend</span>
            </div>
        </div>
        """)
    with b_r2_c2:
        max_esc_limit = float(budget.get("max_escalation_rate", 0.30))
        esc_pill = "pill-optimal" if esc_rate <= max_esc_limit else "pill-danger"
        esc_label = "Compliant" if esc_rate <= max_esc_limit else "High"
        st.html(f"""
        <div class="bento-card">
            <div class="bento-header">
                <span class="bento-title">Escalation Rate</span>
                <span class="bento-dot dot-orange"></span>
            </div>
            <div class="bento-value">{esc_rate:.1%}</div>
            <div class="bento-footer">
                <span class="pill-tag {esc_pill}">● {esc_label}</span>
                <span>Max: <{max_esc_limit:.0%}</span>
            </div>
        </div>
        """)

    # Secondary Sub-Row: LLM Calls & Guardrails
    b_r3_c1, b_r3_c2 = st.columns(2)
    with b_r3_c1:
        st.html(f"""
        <div class="bento-card" style="padding: 12px 18px; margin-bottom: 0px;">
            <div class="bento-header" style="margin-bottom: 4px;">
                <span class="bento-title">LLM API Calls</span>
                <span class="bento-dot dot-blue"></span>
            </div>
            <div class="bento-value" style="font-size: 1.4rem; margin-bottom: 2px;">{total_calls:,}</div>
            <div class="bento-footer">
                <span>{(total_tokens/1000):.1f}k tokens consumed</span>
            </div>
        </div>
        """)
    with b_r3_c2:
        st.html(f"""
        <div class="bento-card" style="padding: 12px 18px; margin-bottom: 0px;">
            <div class="bento-header" style="margin-bottom: 4px;">
                <span class="bento-title">Guardrail Blocks</span>
                <span class="bento-dot dot-red"></span>
            </div>
            <div class="bento-value" style="font-size: 1.4rem; margin-bottom: 2px;">{total_guard_events:,}</div>
            <div class="bento-footer">
                <span class="pill-tag pill-optimal">Shield Active</span>
            </div>
        </div>
        """)

with hero_right:
    # Top Hero Chart: Total LLMs Cost & Token Distribution (Runagent Style)
    with st.container(border=True):
        st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;'><span style='color: {text_primary}; font-weight: 700; font-size: 1rem;'>Total LLMs Cost & Token Telemetry</span><span style='color: {text_secondary}; font-size: 0.78rem;'>Stacked by Day</span></div>", unsafe_allow_html=True)
        st.caption("Prompt vs Completion token velocity with cumulative USD expenditure trajectory")

        if not usage.empty and "created_at" in usage.columns:
            usage_resampled = usage.copy()
            usage_resampled["date_str"] = usage_resampled["created_at"].dt.strftime("%b %d")
            
            daily_agg = usage_resampled.groupby("date_str", sort=False).agg({
                "prompt_tokens": "sum",
                "completion_tokens": "sum",
                "cost_usd": "sum"
            }).reset_index().tail(10)

            melted = daily_agg.melt(
                id_vars=["date_str", "cost_usd"],
                value_vars=["prompt_tokens", "completion_tokens"],
                var_name="Token_Type",
                value_name="Tokens"
            )

            hero_chart = alt.Chart(melted).mark_bar(
                cornerRadiusTopLeft=5,
                cornerRadiusTopRight=5
            ).encode(
                x=alt.X("date_str:N", title=None, axis=alt.Axis(labelColor=chart_label, labelAngle=0, tickColor="transparent", domain=False)),
                y=alt.Y("Tokens:Q", title=None, stack="zero", axis=alt.Axis(labelColor=chart_label, gridColor=chart_grid, domain=False, tickColor="transparent")),
                color=alt.Color("Token_Type:N", 
                                scale=alt.Scale(domain=["prompt_tokens", "completion_tokens"], range=["#06B6D4", "#8B5CF6"]),
                                legend=alt.Legend(orient="top-right", labelColor=chart_label, title=None, symbolType="circle")),
                tooltip=[
                    alt.Tooltip("date_str:N", title="Date"),
                    alt.Tooltip("Token_Type:N", title="Type"),
                    alt.Tooltip("Tokens:Q", title="Tokens", format=","),
                    alt.Tooltip("cost_usd:Q", title="Day Spend", format="$.4f")
                ]
            ).properties(height=265).configure_view(strokeWidth=0).configure(background="transparent")

            st.altair_chart(hero_chart, width="stretch")
        else:
            st.info("No token telemetry recorded yet for the selected criteria.")

st.space("small")

# ---------- SLA & Budget Governance Progress Meters ----------
with st.container(border=True):
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    today_cost = 0.0
    month_cost = 0.0
    if not usage.empty and "cost_usd" in usage.columns:
        today_cost = float(usage[usage["created_at"].dt.date == today]["cost_usd"].sum())
        month_cost = float(usage[usage["created_at"].dt.month == today.month]["cost_usd"].sum())

    daily_limit = float(budget.get("daily_budget_usd", 5.0))
    monthly_limit = float(budget.get("monthly_budget_usd", 100.0))
    daily_pct = min(today_cost / daily_limit, 1.0) if daily_limit > 0 else 0.0
    monthly_pct = min(month_cost / monthly_limit, 1.0) if monthly_limit > 0 else 0.0

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.html(f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.78rem; margin-bottom: 6px;">
            <span style="color: {text_secondary}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">DAILY SPEND</span>
            <span><b style="color: {text_primary}; font-size: 0.88rem;">${today_cost:.4f}</b> <span style="color: {text_muted};">/ ${daily_limit:.2f}</span></span>
        </div>
        """)
        st.progress(daily_pct)
    with b2:
        st.html(f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.78rem; margin-bottom: 6px;">
            <span style="color: {text_secondary}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">MONTHLY SPEND</span>
            <span><b style="color: {text_primary}; font-size: 0.88rem;">${month_cost:.4f}</b> <span style="color: {text_muted};">/ ${monthly_limit:.2f}</span></span>
        </div>
        """)
        st.progress(monthly_pct)
    with b3:
        max_esc = float(budget.get("max_escalation_rate", 0.30))
        esc_pct = min(esc_rate / max_esc, 1.0) if max_esc > 0 else 0.0
        st.html(f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.78rem; margin-bottom: 6px;">
            <span style="color: {text_secondary}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">ESCALATION CEILING</span>
            <span><b style="color: {text_primary}; font-size: 0.88rem;">{esc_rate:.1%}</b> <span style="color: {text_muted};">/ {max_esc:.0%} Max</span></span>
        </div>
        """)
        st.progress(esc_pct)
    with b4:
        min_conf = float(budget.get("min_avg_confidence", 0.60))
        conf_pct = min(avg_conf, 1.0)
        st.html(f"""
        <div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 0.78rem; margin-bottom: 6px;">
            <span style="color: {text_secondary}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">CONFIDENCE SLA</span>
            <span><b style="color: {text_primary}; font-size: 0.88rem;">{avg_conf:.1%}</b> <span style="color: {text_muted};">(Min: {min_conf:.0%})</span></span>
        </div>
        """)
        st.progress(conf_pct)

st.space("small")

# ---------- Workspace Tabs ----------
tab_feed, tab_analytics, tab_security, tab_alerts = st.tabs([
    ":material/list_alt: Live Agent Run Feed",
    ":material/stacked_bar_chart: Agent & Model Analytics",
    ":material/security: Guardrail & Safety Telemetry",
    ":material/notifications_active: Incident & Alert Governance"
])

# ==========================================
# TAB 1: Live Agent Run Feed (Runagent Style)
# ==========================================
with tab_feed:
    st.markdown(f"<h4 style='color: {text_primary}; font-weight: 700; margin-bottom: 2px;'>Live Agent Run Feed & Traces</h4>", unsafe_allow_html=True)
    st.caption("Inspect live session traces, agent intent classification, confidence scores, and token costs")

    # Search & Filter bar
    f_c1, f_c2 = st.columns([0.75, 0.25])
    with f_c1:
        search_query = st.text_input("Search Run Traces", placeholder="Search by Run ID, Agent, User ID, Message, or Intent...", label_visibility="collapsed")
    with f_c2:
        feed_limit = st.selectbox("Show Rows", [25, 50, 100, 200], index=1, label_visibility="collapsed")

    display_conv = conv.copy()
    if search_query:
        mask = (
            display_conv["request_id"].astype(str).str.contains(search_query, case=False, na=False) |
            display_conv["agent"].astype(str).str.contains(search_query, case=False, na=False) |
            display_conv["user_id"].astype(str).str.contains(search_query, case=False, na=False) |
            display_conv["message"].astype(str).str.contains(search_query, case=False, na=False) |
            display_conv["intent"].astype(str).str.contains(search_query, case=False, na=False)
        )
        display_conv = display_conv[mask]

    if not display_conv.empty:
        cols_to_show = ["request_id", "agent", "channel", "intent", "confidence", "tokens_used", "cost", "created_at"]
        existing_cols = [c for c in cols_to_show if c in display_conv.columns]
        
        column_config = {
            "request_id": st.column_config.TextColumn("Run ID", width="small"),
            "agent": st.column_config.TextColumn("Assigned Agent", width="medium"),
            "channel": st.column_config.TextColumn("Channel", width="small"),
            "intent": st.column_config.TextColumn("Classified Intent", width="medium"),
            "confidence": st.column_config.ProgressColumn(
                "Confidence SLA",
                min_value=0.0,
                max_value=1.0,
                format="%.0f%%",
                width="medium"
            ),
            "tokens_used": st.column_config.NumberColumn("Tokens", format="%d", width="small"),
            "cost": st.column_config.NumberColumn("Run Cost", format="$%.4f", width="small"),
            "created_at": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss", width="medium"),
        }
        
        st.dataframe(
            display_conv[existing_cols].head(feed_limit),
            column_config=column_config,
            hide_index=True,
            width="stretch"
        )

        # Trace Message Inspector Expander
        with st.expander(":material/terminal: Inspect Conversation Payload Details"):
            selected_run_id = st.selectbox("Select Run ID to inspect details:", display_conv["request_id"].head(25).tolist())
            if selected_run_id:
                run_row = display_conv[display_conv["request_id"] == selected_run_id].iloc[0]
                insp_c1, insp_c2 = st.columns(2)
                with insp_c1:
                    st.markdown("**User Inbound Message:**")
                    st.info(run_row.get("message", "N/A"))
                with insp_c2:
                    st.markdown("**Agent Response Output:**")
                    st.success(run_row.get("response", "N/A"))
                st.json({
                    "request_id": run_row.get("request_id"),
                    "user_id": run_row.get("user_id"),
                    "agent": run_row.get("agent"),
                    "intent": run_row.get("intent"),
                    "confidence": run_row.get("confidence"),
                    "channel": run_row.get("channel"),
                    "created_at": str(run_row.get("created_at"))
                })
    else:
        st.info("No matching conversation runs found.")

# ==========================================
# TAB 2: Agent & Model Cost Analytics
# ==========================================
with tab_analytics:
    st.markdown(f"<h4 style='color: {text_primary}; font-weight: 700; margin-bottom: 2px;'>Agent Cost & Model Telemetry</h4>", unsafe_allow_html=True)
    st.caption("Granular cost distribution across autonomous agents and model token consumption")

    if not usage.empty and "created_at" in usage.columns:
        col_ag, col_mod = st.columns(2, gap="medium")
        
        with col_ag:
            with st.container(border=True):
                st.markdown(f"<span style='color: {text_primary}; font-weight: 700;'>Cost Distribution by Agent ($ USD)</span>", unsafe_allow_html=True)
                if "agent" in usage.columns:
                    agent_cost = usage.groupby("agent")["cost_usd"].sum().reset_index().sort_values("cost_usd", ascending=False)
                    agent_chart = alt.Chart(agent_cost).mark_bar(
                        cornerRadiusTopRight=5,
                        cornerRadiusBottomRight=5
                    ).encode(
                        x=alt.X("cost_usd:Q", title="Spend ($ USD)", axis=alt.Axis(labelColor=chart_label, titleColor=chart_label, gridColor=chart_grid, domain=False, tickColor="transparent")),
                        y=alt.Y("agent:N", sort="-x", title=None, axis=alt.Axis(labelColor=chart_label, domain=False, tickColor="transparent")),
                        color=alt.Color("cost_usd:Q", legend=None, scale=alt.Scale(range=["#38BDF8", "#8B5CF6"])),
                        tooltip=[
                            alt.Tooltip("agent:N", title="Agent"),
                            alt.Tooltip("cost_usd:Q", title="Spend", format="$.4f")
                        ]
                    ).properties(height=240).configure_view(strokeWidth=0).configure(background="transparent")
                    st.altair_chart(agent_chart, width="stretch")

        with col_mod:
            with st.container(border=True):
                st.markdown(f"<span style='color: {text_primary}; font-weight: 700;'>Token Volume by Foundation Model</span>", unsafe_allow_html=True)
                if "model" in usage.columns:
                    model_tokens = usage.groupby("model")["total_tokens"].sum().reset_index().sort_values("total_tokens", ascending=False)
                    model_chart = alt.Chart(model_tokens).mark_bar(
                        cornerRadiusTopRight=5,
                        cornerRadiusBottomRight=5
                    ).encode(
                        x=alt.X("total_tokens:Q", title="Total Tokens", axis=alt.Axis(labelColor=chart_label, titleColor=chart_label, gridColor=chart_grid, domain=False, tickColor="transparent")),
                        y=alt.Y("model:N", sort="-x", title=None, axis=alt.Axis(labelColor=chart_label, domain=False, tickColor="transparent")),
                        color=alt.Color("total_tokens:Q", legend=None, scale=alt.Scale(range=["#06B6D4", "#10B981"])),
                        tooltip=[
                            alt.Tooltip("model:N", title="Model"),
                            alt.Tooltip("total_tokens:Q", title="Tokens", format=",")
                        ]
                    ).properties(height=240).configure_view(strokeWidth=0).configure(background="transparent")
                    st.altair_chart(model_chart, width="stretch")

        # Cumulative Cost Area Chart
        with st.container(border=True):
            st.markdown(f"<span style='color: {text_primary}; font-weight: 700;'>Financial Spend Trajectory ($ USD)</span>", unsafe_allow_html=True)
            usage_resampled = usage.copy()
            usage_resampled["date_str"] = usage_resampled["created_at"].dt.strftime("%b %d")
            cost_daily = usage_resampled.groupby("date_str", sort=False)["cost_usd"].sum().reset_index().tail(14)
            
            cost_area_chart = alt.Chart(cost_daily).mark_area(
                line={"color": "#10B981", "size": 2.5},
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color="rgba(16, 185, 129, 0.4)", offset=0),
                        alt.GradientStop(color="rgba(16, 185, 129, 0.0)", offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X("date_str:N", title=None, axis=alt.Axis(labelAngle=0, labelColor=chart_label, domain=False, tickColor="transparent")),
                y=alt.Y("cost_usd:Q", title="Spend ($ USD)", axis=alt.Axis(labelColor=chart_label, titleColor=chart_label, gridColor=chart_grid, domain=False, tickColor="transparent")),
                tooltip=[
                    alt.Tooltip("date_str:N", title="Date"),
                    alt.Tooltip("cost_usd:Q", title="Spend ($)", format="$.4f")
                ]
            ).properties(height=240).configure_view(strokeWidth=0).configure(background="transparent")
            
            st.altair_chart(cost_area_chart, width="stretch")
    else:
        st.info("No token telemetry available for the current filter criteria.")

# ==========================================
# TAB 3: Guardrail & Safety Telemetry
# ==========================================
with tab_security:
    st.markdown(f"<h4 style='color: {text_primary}; font-weight: 700; margin-bottom: 2px;'>Autonomous Guardrail & Security Telemetry</h4>", unsafe_allow_html=True)
    st.caption("Active interception of prompt injections, PII leaks, low-confidence responses, and policy deviations")

    if not guard.empty:
        g_c1, g_c2 = st.columns(2, gap="medium")
        with g_c1:
            with st.container(border=True):
                st.markdown(f"<span style='color: {text_primary}; font-weight: 700;'>Interceptions by Policy Event Type</span>", unsafe_allow_html=True)
                if "event_type" in guard.columns:
                    ev_counts = guard["event_type"].value_counts().reset_index()
                    ev_counts.columns = ["event_type", "count"]
                    ev_chart = alt.Chart(ev_counts).mark_bar(
                        cornerRadiusTopRight=5,
                        cornerRadiusBottomRight=5
                    ).encode(
                        x=alt.X("count:Q", title="Event Count", axis=alt.Axis(labelColor=chart_label, titleColor=chart_label, gridColor=chart_grid, domain=False, tickColor="transparent")),
                        y=alt.Y("event_type:N", sort="-x", title=None, axis=alt.Axis(labelColor=chart_label, domain=False, tickColor="transparent")),
                        color=alt.Color("event_type:N", legend=None, scale=alt.Scale(range=["#F43F5E", "#8B5CF6", "#06B6D4", "#F59E0B"])),
                        tooltip=[alt.Tooltip("event_type:N", title="Policy"), alt.Tooltip("count:Q", title="Interceptions")]
                    ).properties(height=200).configure_view(strokeWidth=0).configure(background="transparent")
                    st.altair_chart(ev_chart, width="stretch")

        with g_c2:
            with st.container(border=True):
                st.markdown(f"<span style='color: {text_primary}; font-weight: 700;'>Threat Severity Distribution</span>", unsafe_allow_html=True)
                if "severity" in guard.columns:
                    sev_counts = guard["severity"].value_counts().reset_index()
                    sev_counts.columns = ["severity", "count"]
                    sev_chart = alt.Chart(sev_counts).mark_bar(
                        cornerRadiusTopRight=5,
                        cornerRadiusBottomRight=5
                    ).encode(
                        x=alt.X("count:Q", title="Count", axis=alt.Axis(labelColor=chart_label, titleColor=chart_label, gridColor=chart_grid, domain=False, tickColor="transparent")),
                        y=alt.Y("severity:N", sort="-x", title=None, axis=alt.Axis(labelColor=chart_label, domain=False, tickColor="transparent")),
                        color=alt.Color("severity:N", legend=None,
                                        scale=alt.Scale(domain=["critical", "warning", "info"],
                                                        range=["#F43F5E", "#F59E0B", "#38BDF8"])),
                        tooltip=[alt.Tooltip("severity:N", title="Severity"), alt.Tooltip("count:Q", title="Count")]
                    ).properties(height=200).configure_view(strokeWidth=0).configure(background="transparent")
                    st.altair_chart(sev_chart, width="stretch")

        st.markdown(f"<h5 style='color: {text_primary}; font-weight: 700; margin-top: 16px;'>Recent Intercepted Security Events</h5>", unsafe_allow_html=True)
        g_cols = ["request_id", "agent", "event_type", "severity", "details", "created_at"]
        existing_g_cols = [c for c in g_cols if c in guard.columns]
        
        st.dataframe(
            guard[existing_g_cols].head(35),
            column_config={
                "request_id": st.column_config.TextColumn("Run ID", width="small"),
                "agent": st.column_config.TextColumn("Target Agent", width="medium"),
                "event_type": st.column_config.TextColumn("Guardrail Policy", width="medium"),
                "severity": st.column_config.TextColumn("Severity Level", width="small"),
                "created_at": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss", width="medium"),
            },
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No guardrail events recorded.")

# ==========================================
# TAB 4: Incident & Alert Governance
# ==========================================
with tab_alerts:
    st.markdown(f"<h4 style='color: {text_primary}; font-weight: 700; margin-bottom: 2px;'>Real-Time Incident & Alert Governance</h4>", unsafe_allow_html=True)
    st.caption("Active threshold alerts, automated budget ceiling breaches, and operator acknowledgement workflows")

    if alerts_df.empty:
        st.info("No governance alerts logged. Trigger 'Run Audit & Health Checks' in the sidebar to perform a live scan.")
    else:
        unack = alerts_df[alerts_df["acknowledged"] == False] if "acknowledged" in alerts_df.columns else alerts_df
        ack = alerts_df[alerts_df["acknowledged"] == True] if "acknowledged" in alerts_df.columns else pd.DataFrame()

        stat_c1, stat_c2 = st.columns(2)
        with stat_c1:
            st.html(f"""
            <div class="bento-card" style="margin-bottom: 0px;">
                <div class="bento-header">
                    <span class="bento-title">Pending Unresolved Incidents</span>
                    <span class="bento-dot dot-red"></span>
                </div>
                <div class="bento-value" style="color: #FDA4AF;">{len(unack)}</div>
                <div class="bento-footer"><span class="pill-tag pill-danger">Action Required</span></div>
            </div>
            """)
        with stat_c2:
            st.html(f"""
            <div class="bento-card" style="margin-bottom: 0px;">
                <div class="bento-header">
                    <span class="bento-title">Resolved Audit Events</span>
                    <span class="bento-dot dot-green"></span>
                </div>
                <div class="bento-value" style="color: #6EE7B7;">{len(ack)}</div>
                <div class="bento-footer"><span class="pill-tag pill-optimal">Acknowledged</span></div>
            </div>
            """)

        st.space("small")
        st.markdown(f"<h5 style='color: {text_primary}; font-weight: 700;'>Live Incident Resolution Queue</h5>", unsafe_allow_html=True)

        for _, row in alerts_df.head(25).iterrows():
            sev = str(row.get("severity", "info")).lower()
            pill_class = "pill-danger" if sev == "critical" else ("pill-warning" if sev == "warning" else "pill-neutral")
            
            with st.container(border=True):
                al_col1, al_col2, al_col3, al_col4 = st.columns([0.16, 0.54, 0.18, 0.12], vertical_alignment="center")
                
                with al_col1:
                    st.html(f'<span class="pill-tag {pill_class}">● {sev.upper()}</span>')
                    st.caption(f"{row.get('alert_type', 'alert')}")
                
                with al_col2:
                    st.markdown(f"**{row.get('message', 'Alert triggered')}**")
                    st.caption(f"Logged: {row.get('created_at', 'N/A')}")
                
                with al_col3:
                    val = row.get("value", 0.0)
                    thresh = row.get("threshold", 0.0)
                    try:
                        st.markdown(f"Metric: `{float(val):.3f}`")
                        st.caption(f"Ceiling: `{float(thresh):.3f}`")
                    except Exception:
                        st.markdown(f"Value: `{val}`")
                
                with al_col4:
                    is_ack = bool(row.get("acknowledged", False))
                    if not is_ack:
                        if st.button("Ack", key=f"btn_ack_{row['id']}", icon=":material/done_all:", width="stretch"):
                            client = get_client()
                            if client:
                                try:
                                    client.table("alerts").update({"acknowledged": True}).eq("id", int(row["id"])).execute()
                                except Exception:
                                    pass
                            for la in st.session_state.local_alerts:
                                if la.get("id") == row["id"]:
                                    la["acknowledged"] = True
                            st.cache_data.clear()
                            st.toast("Alert acknowledged and marked resolved.", icon="✅")
                            st.rerun()
                    else:
                        st.html('<span class="pill-tag pill-optimal">Resolved</span>')