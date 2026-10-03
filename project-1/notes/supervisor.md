# Supervisor - Design Note

## Purpose
Single entry point for all customer messages. Routes to the correct agent based on intent.

## Pipeline
1. Webhook receives message
2. Normalize input
3. Fast Triage (regex) classifies intent
4. IF booking -> Call Booking Agent
5. IF faq -> Call Support Agent
6. ELSE (complaint/emergency) -> Call Escalation Agent
7. Return agent response to caller

## Tools
- Fast Triage (regex, no LLM, fast + cheap)
- HTTP Request calls each specialist agent
- Each agent handles its own DB writes and logging

## Memory
Stateless. Each agent manages its own memory.

## Permissions
- Read: incoming message
- Route: cannot write directly to DB

## Failure Handling
- Unknown intent -> default to faq (Support Agent handles low-confidence escalation)
- Agent call fails -> returns error from HTTP node

## Why Separate Agent
- Single entry point for channels (WhatsApp, SMS, email)
- Agents stay decoupled
- Routing logic can be tuned without touching agents

## Alternatives Considered
- LLM-based triage -> rejected (regex is 10x faster and free)
- Direct agent calls from channels -> rejected (duplicate routing)
