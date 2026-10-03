Project 3 - AI Ops Dashboard
Covered job requirement: monitoring, guardrails, cost control, and security for production AI.

Problem
Project 1 is a multi-agent customer support system (n8n + Supabase + OpenRouter). It logs conversations to a conversations table but provides no visibility into:

which agents are active and at what cost

how often LLM outputs are rejected or escalated

whether daily spend is on track

whether quality (confidence) is drifting

Solution
A standalone Streamlit dashboard that reads from Supabase and surfaces:

Volume KPIs - conversations, LLM calls, tokens, total cost, guardrail events

Cost over time - rolling daily spend

Cost attribution - per agent and per model

Guardrail analysis - events by type (qa_reject, low_confidence, pii_flagged, blocked) and severity

Live alert checks - today cost vs daily budget, escalation rate vs max, avg confidence vs min

Alert history + Ack workflow - persisted in alerts table with acknowledgment

Architecture
text
Project 1 (n8n agents) ---> conversations ---+
                                              |
Project 3 tracker --------> token_usage ------+--> Streamlit Dashboard
                           guardrail_events --+         |
                           budget_config -----+         v
                           alerts <-----------+   thresholds + Ack
Key decision: Project 3 does not touch Project 1 workflows. Tracking is added as a separate, additive layer - the same way production teams bolt observability onto existing services rather than rewriting them.

Data sources
Table	Origin	Rows (demo)
conversations	Project 1	54
token_usage	Project 3 (seeded from realistic distribution)	200
guardrail_events	Backfilled from conversations + seeded	40+
budget_config	Project 3	1
alerts	Live-generated on breach	1+
Alert rules
Rule	Trigger	Severity
daily_budget	today cost > daily_budget_usd	critical
escalation_rate	escalation intent share > max_escalation_rate	warning
confidence_drop	avg confidence < min_avg_confidence	warning
Guardrail derivation
The backfill script scans conversations.response and confidence:

"Escalated: low confidence" -> low_confidence event

"Escalated: complaint" -> blocked (critical)

"Escalated: high_value_refund" -> blocked (critical)

Security notes
Dashboard uses the service_role key server-side only (local Streamlit).

Key lives in .env (root), never committed (.gitignore).

Public anon path remains RLS-protected - dashboard is the only component with elevated read.

Future work
Wire n8n QA Agent to POST to guardrail_events in real time (replaces backfill).

Replace seeded token_usage with live OpenRouter usage emitted by a new HTTP-based LLM node.

Add Slack/email notification on critical alerts.

Add per-user cost attribution.

Stack
Python 3.14 - Streamlit 1.64 - supabase-py 2.31 - pandas 3.0 - Postgres (Supabase)

