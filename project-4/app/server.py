"""
Fast ASGI backend server for the Voice Agent.
Connects the Next.js frontend with the core speech/supervisor services:
  - Deepgram STT (speech-to-text)
  - Edge-TTS (text-to-speech)
  - n8n Supervisor Webhook
  - Supabase Voice Call Logging
"""

import sys
import os
import time
from pathlib import Path

# Ensure project-4 is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route

from app.core.config import STT_MODEL, TTS_VOICE, check_config
from app.core.voice_io import transcribe, synthesize, call_supervisor
from app.core.logger import log_voice_call


async def stt_endpoint(request):
    """
    POST /api/stt
    Accepts raw audio bytes (audio/webm, audio/wav, etc.) and transcribes via Deepgram.
    """
    try:
        t0 = time.perf_counter()
        audio_bytes = await request.body()
        if not audio_bytes:
            return JSONResponse({"error": "No audio received"}, status_code=400)

        content_type = request.headers.get("content-type", "audio/webm")
        # Strip parameters like ';codecs=opus' if present
        mime_clean = content_type.split(";")[0].strip()

        transcript, latency_ms = transcribe(audio_bytes, mimetype=mime_clean)
        return JSONResponse({
            "transcript": transcript,
            "latency": latency_ms,
            "confidence": 1.0 if transcript else 0.0,
        })
    except Exception as e:
        return JSONResponse({"error": f"STT failed: {str(e)}"}, status_code=500)


async def tts_endpoint(request):
    """
    POST /api/tts
    Accepts JSON {"text": "..."} and returns synthesized MP3 audio bytes.
    """
    try:
        body = await request.json()
        text = body.get("text", "").strip()
        if not text:
            return JSONResponse({"error": "Text is required"}, status_code=400)

        voice = body.get("voice", TTS_VOICE)
        audio_bytes, latency_ms = synthesize(text, voice=voice)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "X-Latency": str(latency_ms),
                "Content-Disposition": 'inline; filename="response.mp3"',
            },
        )
    except Exception as e:
        return JSONResponse({"error": f"TTS failed: {str(e)}"}, status_code=500)


import re
from datetime import datetime, timedelta

OUT_OF_SCOPE_RESPONSE = (
    "Sorry, I cannot help you with that. I am your Nexio24 customer assistant and can help you "
    "make a reservation, check your booking status, or answer questions about our opening hours, "
    "refunds, and support policies. Would you like to book a table or check an existing reservation?"
)

def is_greeting(text: str) -> bool:
    clean = text.lower().strip()
    pattern = r"^(hello|hi|hey|good morning|good afternoon|good evening|howdy|greetings|hola)\b"
    return bool(re.search(pattern, clean)) or clean in ["hello", "hi", "hey", "yo"]

def is_clarification(text: str) -> bool:
    clean = text.lower().strip()
    patterns = [
        r"^(what|what's|how)\s+(do\s+you\s+mean|you\s+mean|does\s+that\s+mean)",
        r"^(i\s+don'?t\s+understand|explain|pardon|huh\??|what\??|what\s+now)$",
        r"^(can\s+you\s+clarify|what\s+can\s+you\s+do|help\s+me)$",
    ]
    return any(re.search(p, clean) for p in patterns) or clean in ["what", "what?", "huh", "huh?", "pardon", "what you mean", "what do you mean"]

def is_status_check(text: str) -> bool:
    clean = text.lower().strip()
    patterns = [
        r"(did|is|has).*(order|booking|reservation).*(book|confirm|place|go through|succeed)",
        r"(check|track|view|see|status of|find).*(order|booking|reservation)",
        r"(order|booking|reservation).*(status|confirmed)",
    ]
    return any(re.search(p, clean) for p in patterns)

def is_booking_request(text: str) -> bool:
    clean = text.lower().strip()
    return bool(re.search(r"\b(book|booking|reserve|reservation|appointment|table)\b", clean))

def parse_booking_details(text: str):
    clean = text.lower()
    
    # 1. Party size
    party_size = None
    party_match = re.search(r"(\d+)\s*(?:people|guests|persons|person|seats|pax|party)", clean)
    if not party_match:
        party_match = re.search(r"(?:for|party of|table for)\s*(\d+)", clean)
    if party_match:
        try:
            party_size = int(party_match.group(1))
        except ValueError:
            pass
            
    # 2. Date
    date_str = None
    now = datetime.now()
    if "tomorrow" in clean:
        date_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "today" in clean or "tonight" in clean:
        date_str = now.strftime("%Y-%m-%d")
    else:
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", clean)
        if date_match:
            date_str = date_match.group(1)

    # 3. Time
    time_str = None
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", clean)
    if time_match:
        hr = int(time_match.group(1))
        mn = int(time_match.group(2) or 0)
        ampm = time_match.group(3)
        if ampm == "pm" and hr < 12:
            hr += 12
        elif ampm == "am" and hr == 12:
            hr = 0
        time_str = f"{hr:02d}:{mn:02d}"
    else:
        time_match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", clean)
        if time_match_24:
            time_str = f"{int(time_match_24.group(1)):02d}:{time_match_24.group(2)}"

    return {
        "date": date_str,
        "time": time_str,
        "party_size": party_size,
    }

def create_booking(user_id: str, date: str, time: str, party_size: int):
    try:
        from app.core.logger import _sb
        res = _sb().table("bookings").insert({
            "user_id": user_id or "guest",
            "date": date,
            "time": time,
            "party_size": party_size or 2,
            "status": "confirmed"
        }).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        print(f"[server] Error creating booking: {e}")
        return None

def query_latest_booking():
    try:
        from app.core.logger import _sb
        res = _sb().table("bookings").select("*").order("id", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        print(f"[server] Error querying bookings: {e}")
        return None

def match_faq(text: str) -> str | None:
    clean = text.lower().strip()
    if re.search(r"\b(refund|refunds|money back|return policy)\b", clean):
        return (
            "Refunds are available within 30 days of purchase. Note that refunds exceeding $100 "
            "require manager approval. Would you like assistance initiating a refund request?"
        )
    if re.search(r"\b(hour|hours|open|opening|close|closing|schedule)\b", clean):
        return (
            "We are open 24/7 for urgent customer support. Our standard support hours are "
            "9:00 AM to 6:00 PM Monday through Friday."
        )
    if re.search(r"\b(booking policy|cancellation|cancellations|how far in advance|cancel booking)\b", clean):
        return (
            "Bookings can be made up to 7 days in advance. Cancellations must be made "
            "at least 24 hours before the scheduled booking time."
        )
    if re.search(r"\b(contact|email|phone|call us|support email|hotline|phone number)\b", clean):
        return (
            "For urgent issues, please call our emergency support line. For general inquiries, "
            "you can email us at support@nexio24.com."
        )
    if re.search(r"\b(reset password|forgot password|change password|login issue|cannot login|can't login)\b", clean):
        return (
            "To reset your password, click 'Forgot Password' on the login page. "
            "A secure reset link will be emailed to you within 5 minutes."
        )
    return None


async def supervisor_endpoint(request):
    """
    POST /api/supervisor
    Accepts JSON {"text": "...", "sessionId": "..."}
    Handles greetings, booking status lookups, n8n multi-agent routing, and guided fallback.
    """
    try:
        body = await request.json()
        text = (body.get("text") or body.get("message", "")).strip()
        session_id = body.get("sessionId") or request.headers.get("X-Session-Id", "unknown")

        if not text:
            return JSONResponse({"error": "Message text is required"}, status_code=400)

        t0 = time.perf_counter()
        agent_name = "supervisor"
        status = "ok"
        error_msg = None
        conv_id = session_id

        # 1. Handle Greetings
        if is_greeting(text):
            response_text = (
                "Hello! How may I help you today? I can help you make a table reservation, "
                "check your booking status, or answer questions about our hours and policies."
            )
            agent_name = "greeting_agent"
            sup_ms = int((time.perf_counter() - t0) * 1000)

        # 2. Handle Clarifications ("what you mean", "what do you mean", etc.)
        elif is_clarification(text):
            response_text = (
                "I apologize for the confusion! I am your Nexio24 customer assistant. "
                "I can help you reserve a table, check your booking status, or answer questions "
                "about our opening hours, refund policies, and support services. How may I help you?"
            )
            agent_name = "support_agent"
            sup_ms = int((time.perf_counter() - t0) * 1000)

        # 3. Handle Direct Knowledge Base / FAQ Queries (e.g. Refund Policy, Hours, Contact)
        elif match_faq(text):
            response_text = match_faq(text)
            agent_name = "faq_agent"
            sup_ms = int((time.perf_counter() - t0) * 1000)

        # 4. Handle Booking / Order Status Lookup
        elif is_status_check(text):
            booking = query_latest_booking()
            if booking:
                b_id = booking.get("id", "")
                date_val = booking.get("date", "upcoming date")
                time_val = booking.get("time", "")
                party_val = booking.get("party_size", 2)
                b_status = booking.get("status", "confirmed")
                response_text = (
                    f"Yes, your reservation is confirmed! Booking #{b_id} is scheduled for "
                    f"{party_val} guests on {date_val} at {time_val} (Status: {b_status})."
                )
            else:
                response_text = (
                    "I checked our reservation records, but could not find an active booking under your profile. "
                    "Would you like to book a table now?"
                )
            agent_name = "booking_status_agent"
            sup_ms = int((time.perf_counter() - t0) * 1000)

        # 5. Handle Booking & Table Reservation Requests
        elif is_booking_request(text):
            details = parse_booking_details(text)
            if details["date"] and details["time"]:
                party = details["party_size"] or 2
                created = create_booking(session_id, details["date"], details["time"], party)
                b_id = created.get("id") if created else "NEW"
                response_text = (
                    f"Your reservation is confirmed! Booking #{b_id} has been scheduled for "
                    f"{party} guests on {details['date']} at {details['time']}. We look forward to hosting you!"
                )
                agent_name = "booking_agent"
            else:
                response_text = (
                    "I would be happy to help you book a table! Could you please let me know:\n"
                    "- What date would you like to book for?\n"
                    "- What time?\n"
                    "- How many guests will be in your party?"
                )
                agent_name = "booking_agent"
            sup_ms = int((time.perf_counter() - t0) * 1000)

        # 6. Route to n8n Supervisor / Out-of-Scope Fallback
        else:
            try:
                response_text, conv_id, sup_ms = call_supervisor(text)
                clean_resp = (response_text or "").lower()

                # Check if n8n returned low-confidence, unhandled escalation, or echoed question
                is_out_of_scope = any(phrase in clean_resp for phrase in [
                    "didn't quite catch that",
                    "outside what i can help with",
                    "couldn't find an answer",
                    "not sure i understood",
                    "low_confidence",
                    "unclear_intent"
                ]) or (clean_resp == text.lower().strip())

                if is_out_of_scope or not response_text:
                    faq_match = match_faq(text)
                    if faq_match:
                        response_text = faq_match
                        agent_name = "faq_agent"
                    else:
                        response_text = OUT_OF_SCOPE_RESPONSE
                        agent_name = "fallback_assistant"

            except Exception as e:
                sup_ms = int((time.perf_counter() - t0) * 1000)
                faq_match = match_faq(text)
                if faq_match:
                    response_text = faq_match
                    agent_name = "faq_agent"
                    status = "ok"
                elif is_booking_request(text):
                    response_text = (
                        "I would be happy to help you book a table! Could you please let me know "
                        "what date, time, and number of guests you would like to reserve for?"
                    )
                    agent_name = "booking_agent"
                    status = "ok"
                else:
                    response_text = OUT_OF_SCOPE_RESPONSE
                    agent_name = "fallback_assistant"
                    status = "fallback"
                error_msg = str(e)

        total_ms = int((time.perf_counter() - t0) * 1000)

        # Log conversation turn in Supabase
        try:
            log_voice_call(
                conversation_id=conv_id or session_id,
                transcript=text,
                response_text=response_text,
                stt_model=STT_MODEL,
                tts_model="edge-tts",
                tts_voice=TTS_VOICE,
                supervisor_latency_ms=sup_ms,
                total_latency_ms=total_ms,
                status=status,
                error=error_msg,
            )
        except Exception as log_err:
            print(f"[logger] Supabase logging note: {log_err}")

        return JSONResponse({
            "response": response_text,
            "agent": agent_name,
            "conversation_id": conv_id or session_id,
            "latency": sup_ms,
            "status": status,
        })
    except Exception as e:
        return JSONResponse({"error": f"Supervisor handler failed: {str(e)}"}, status_code=500)


async def health_endpoint(request):
    """
    GET /health
    System check reporting configuration status.
    """
    missing = check_config()
    return JSONResponse({
        "status": "ready" if not missing else "degraded",
        "missing_env_vars": missing,
        "stt_model": STT_MODEL,
        "tts_voice": TTS_VOICE,
    })


async def root_endpoint(request):
    """
    GET /
    Friendly root endpoint providing service status and endpoint links.
    """
    return JSONResponse({
        "service": "Voice Agent API Backend",
        "status": "online",
        "endpoints": {
            "stt": "/api/stt (POST)",
            "tts": "/api/tts (POST)",
            "supervisor": "/api/supervisor (POST)",
            "health": "/health (GET)",
        },
        "frontend_ui": "http://localhost:3000"
    })


routes = [
    Route("/", root_endpoint, methods=["GET"]),
    Route("/api/stt", stt_endpoint, methods=["POST"]),
    Route("/api/tts", tts_endpoint, methods=["POST"]),
    Route("/api/supervisor", supervisor_endpoint, methods=["POST"]),
    Route("/health", health_endpoint, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=5000, reload=True)
