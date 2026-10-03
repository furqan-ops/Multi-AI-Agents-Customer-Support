# Escalation Agent - Design Note

## Purpose
Handle requests that cannot be auto-resolved. Create ticket and notify human.

## Pipeline
1. Receive escalation via webhook
2. Normalize input
3. Log to conversations table
4. Build ticket with priority
5. Notify human

## Tools
- Supabase (log)
- Notification channel (placeholder)

## Memory
Stateless. Logs to conversations table for audit.

## Permissions
- Write: conversations table
- Notify: human on-call

## Failure Handling
- Missing reason -> low_confidence
- Missing confidence -> 0
- Missing agent -> support

## Why Separate Agent
- Centralized human handoff logic
- Single audit point
- Can route to different humans by reason

## Alternatives Considered
- Inline escalation -> duplicate logic
- Auto-resolve everything -> unsafe
