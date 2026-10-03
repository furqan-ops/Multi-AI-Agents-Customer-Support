# Project 1: Multi-Agent Customer Support System

A production-grade multi-agent system built with n8n, Supabase, and OpenRouter. Routes customer messages to 5 specialized AI agents with human fallback.

## Architecture

User Message (WhatsApp/Email)
         |
         v
   [Supervisor]
         |
   Fast Triage (regex)
         |
   +-----+-----+-----+
   |           |     |
   v           v     v
[Booking]  [Support] [Escalation]
   |           |     |
   +-----+-----+-----+
         |
         v
   [QA Agent]
         |
         v
   Response / Human Handoff

## Agents

| Agent | Role | Trigger | Writes To |
|---|---|---|---|
| Triage | Classifies intent | Webhook /triage | conversations |
| RAG Ingestion | Loads FAQ into vector DB | Manual | documents |
| Support | Answers FAQs via RAG | Webhook /support | conversations |
| Escalation | Human handoff with ticket | Webhook /escalate | conversations |
| Booking | Creates reservations | Webhook /booking | bookings, conversations |
| QA | Validates outputs (2-layer) | Webhook /qa | conversations |
| Supervisor | Routes messages | Webhook /supervisor | (none) |

## Tech Stack

- n8n (self-hosted) - orchestration
- Supabase (PostgreSQL + pgvector) - data + vector search
- OpenRouter - LLM + embeddings
- Docker - n8n runtime

## Design Decisions

### Why 7 separate workflows?
- Permission isolation per agent
- Independent scaling
- Failure isolation
- Team ownership

### Two-Layer QA
- Layer 1: Keyword check (deterministic)
- Layer 2: LLM fact-checker
- Both must approve

### Human Fallback
- Support: escalates if confidence < 0.7
- QA: escalates if claim not in context
- Supervisor: complaints/emergencies go to Escalation

## Setup

1. Copy .env.example to .env
2. Add keys: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SECRET_KEY, OPENROUTER_API_KEY
3. Start n8n via Docker with /data mount
4. Import workflows from workflows/ into n8n
5. Activate all 7 workflows
6. Create Supabase tables (see notes/)
7. Test via curl

## Demo Flows

Booking:
POST /webhook/supervisor {"message":"Book a table for 4 tomorrow at 7pm"}
Response: {"status":"confirmed","date":"...","time":"19:00","party_size":4}

FAQ:
POST /webhook/supervisor {"message":"What are your opening hours?"}
Response: {"status":"answered","answer":"...","confidence":1}

Escalation:
POST /webhook/supervisor {"message":"I want a refund of 500 dollars"}
Response: {"ticket_id":"ESC-...","status":"pending_human"}

## Files

- workflows/ - n8n JSON exports
- notes/ - design decisions per agent
- faq.txt - sample data
