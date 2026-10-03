# Booking Agent - Design Note

## Purpose
Extract booking details from natural language, create reservation, ask for missing fields.

## Pipeline
1. Webhook receives message
2. Normalize input
3. LLM extracts date, time, party_size as JSON
4. Parse JSON safely
5. If missing fields -> return questions
6. Else -> insert into bookings table + log to conversations

## Tools
- OpenRouter Chat (openrouter/free)
- Supabase (bookings, conversations)

## Memory
Stateless. Uses user_id in bookings for future lookup.

## Permissions
- Write: bookings table
- Write: conversations table
- Cannot read other users' bookings

## Failure Handling
- Invalid JSON -> treat all fields as missing
- Missing date/time/party_size -> ask user
- DB insert error -> workflow error (should add retry)

## Why Separate Agent
- Isolated write permissions (only bookings)
- Specialized extraction prompt
- Cannot leak other users' data

## Alternatives Considered
- Rule-based regex parsing -> rejected (too brittle)
- Single agent for booking + FAQ -> rejected (permission mixing)
