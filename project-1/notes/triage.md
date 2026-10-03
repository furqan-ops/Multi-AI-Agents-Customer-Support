# Triage Agent — Design Note

## Purpose
Classify incoming user messages into one of 4 intents: booking, faq, complaint, emergency.

## Tools
- LLM only (OpenRouter: meta-llama/llama-3.3-70b-instruct:free)

## Memory
- None. Stateless.

## Permissions
- Read: incoming message
- Write: log to conversations table

## Failure Handling
- Invalid JSON from LLM -> default to escalate with confidence 0
- Unknown intent -> default to escalate

## Why Separate Agent
- Routing decision is independent of task execution
- Allows swapping LLM without affecting downstream agents
- Cheap and fast - can run on small model

## Alternatives Considered
- Single agent with all tools -> rejected (permission isolation impossible)
- Rule-based classifier -> rejected (cannot handle natural language variety)