# QA Agent - Design Note

## Purpose
Validate other agents' outputs. Reject hallucinations and unsafe responses.

## Pipeline
1. Webhook receives agent output + context + user message
2. Normalize input
3. Keyword Check: reject if <50% response keywords appear in context
4. QA Review: LLM strict fact-check
5. Parse QA: BOTH checks must approve
6. Approved -> Log QA + Respond Approved
7. Rejected -> Final Decision -> Respond to Webhook

## Two-Layer Validation
- Keyword Check (deterministic): rejects hallucinated keywords
- LLM QA (strict prompt): rejects unsupported claims
- LLM cannot override Keyword Check

## Tools
- OpenRouter Chat (openrouter/free)
- Supabase (log)

## Permissions
- Read: inputs
- Write: conversations

## Failure Handling
- Keyword Check fails -> forced reject
- LLM JSON invalid -> reject
- IF node bug fixed: only one condition, checks .approved === true

## Why Separate Agent
- Centralized quality gate
- Hybrid deterministic + LLM
- Tunable without touching other agents

## Alternatives Considered
- LLM-only QA -> too lenient
- Keyword-only -> misses paraphrased claims
