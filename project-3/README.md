# Project 3 — AI Ops Dashboard

Streamlit + Supabase dashboard for multi-agent AI observability.

**Covers:** monitoring, guardrails, cost control, security for production AI.

## Features
- Volume + cost KPIs (conversations, LLM calls, tokens, cost, guardrail events)
- Cost over time (daily)
- Cost by agent, tokens by model
- Guardrail events by type + severity
- Live alert checks (daily budget, escalation rate, avg confidence)
- Alert history with Ack workflow

## Quickstart
```powershell
cd project-3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run dashboard\app.py