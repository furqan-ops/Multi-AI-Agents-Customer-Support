# Multi-Agent Performance & Cost Governance Center

An enterprise-grade LLM observability, telemetry, guardrail enforcement, and financial cost governance platform for autonomous multi-agent clusters.

Built with **Python**, **Streamlit 1.64+**, **Supabase PostgreSQL**, **Altair Vega-Lite**, and **Pandas**.

---

## 🌟 Key Features

* **Real-Time Telemetry & Cost Analytics**:
  * Stacked prompt vs. completion token distribution charts over temporal windows.
  * Cumulative USD spend tracking and daily financial trajectories.
  * Granular cost breakdowns across autonomous agents (`booking`, `support`, `triage`, `escalation`, `faq`).
  * Token utilization analytics across foundation models (`gpt-4o-mini`, `text-embedding-3-small`, etc.).
* **Bento Grid Executive KPI Metrics**:
  * Total Conversations / Agent Runs, Inbound LLM Calls, Total Tokens, Cumulative Cost, Average Cost per Run.
  * Real-time Escalation Rate tracking against ceiling thresholds.
  * Agent Confidence Scoring against target SLAs.
  * Intercepted guardrail events and security shielding metrics.
* **Live Agent Run Feed & Traces**:
  * Searchable live traces by Run ID, Agent name, Intent, and Message content.
  * Interactive payload inspector for examining inbound user queries, classification metadata, and agent response outputs.
* **Guardrail & Security Interception Center**:
  * Automated tracking of prompt injections, PII disclosures, low-confidence responses, and policy infractions.
  * Threat severity classification (`critical`, `warning`, `info`).
* **Incident & Alert Governance**:
  * Automated budget ceiling and SLA compliance checks.
  * One-click interactive **Acknowledge (`Ack`)** workflow updating Supabase in real-time.

---

## 🚀 Quickstart (Local Development)

### 1. Environment Variables
Ensure your root `.env` (or `project-3/.env`) contains your Supabase credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-supabase-service-role-or-anon-key
```

### 2. Activate & Run
```powershell
cd project-3
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🌐 Cloud Deployment Guide

### Deploying to Streamlit Community Cloud (Recommended for Python/GitHub)
Since Streamlit is a stateful Python application requiring persistent WebSockets:
1. Push your repository to **GitHub**.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository, set the main file path to `project-3/dashboard/app.py`.
4. In **Advanced Settings**, paste your `SUPABASE_URL` and `SUPABASE_KEY` under Secrets.
5. Click **Deploy** — your live public URL is active in under 60 seconds!