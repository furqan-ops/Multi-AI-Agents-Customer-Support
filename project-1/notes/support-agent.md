# Support Agent — Design Note

## Purpose
Answer user questions using RAG over FAQ documents. Escalate if confidence < 0.7.

## Pipeline
1. Webhook receives question
2. Embed question (text-embedding-3-small via OpenRouter)
3. Vector search top 3 chunks via Supabase RPC match_documents
4. Build context from retrieved chunks
5. LLM generates answer with confidence
6. Confidence < 0.7 -> Log Escalation
7. Confidence >= 0.7 -> Log Success

## Tools
- OpenRouter Embeddings
- Supabase RPC (match_documents)
- OpenRouter Chat (openrouter/free router)

## Memory
Stateless per request. Reads from documents table.

## Permissions
- Read: documents table
- Write: conversations table

## Failure Handling
- Invalid JSON -> confidence 0 -> escalate
- No chunks found -> confidence 0 -> escalate
- Supabase auth: secret key in apikey header only

## Why Separate Agent
- Read-only; cannot modify bookings/users
- Dedicated prompt for citation-based answers
- Tunable escalation threshold

## Alternatives Considered
- Single LLM without RAG -> hallucinations
- Reranking -> deferred (cost)
