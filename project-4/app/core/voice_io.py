import time
import asyncio
import tempfile
import os
import requests
import edge_tts
from app.core.config import (
    DEEPGRAM_API_KEY, SUPERVISOR_URL,
    STT_MODEL, TTS_VOICE,
)

# ---------- STT: Deepgram ----------
def transcribe(audio_bytes: bytes, mimetype: str = "audio/wav") -> tuple[str, int]:
    t0 = time.perf_counter()
    url = f"https://api.deepgram.com/v1/listen?model={STT_MODEL}&smart_format=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": mimetype,
    }
    r = requests.post(url, headers=headers, data=audio_bytes, timeout=60)
    r.raise_for_status()
    ms = int((time.perf_counter() - t0) * 1000)
    data = r.json()
    try:
        text = data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    except (KeyError, IndexError):
        text = ""
    return text, ms


# ---------- TTS: edge-tts ----------
async def _edge_save(text: str, voice: str, path: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)

def synthesize(text: str, voice: str = TTS_VOICE) -> tuple[bytes, int]:
    t0 = time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        out_path = f.name
    try:
        asyncio.run(_edge_save(text, voice, out_path))
        with open(out_path, "rb") as f:
            audio = f.read()
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)
    ms = int((time.perf_counter() - t0) * 1000)
    return audio, ms


# ---------- Supervisor ----------
def call_supervisor(text: str, timeout: int = 60) -> tuple[str, str | None, int]:
    t0 = time.perf_counter()
    r = requests.post(
        SUPERVISOR_URL,
        json={"message": text, "channel": "voice"},
        timeout=timeout,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and data:
        data = data[0]

    conversation_id = data.get("conversation_id") or data.get("id")

    # If it is an escalation ticket or marked for human review
    if data.get("status") == "pending_human" or data.get("ticket_id"):
        ticket_id = data.get("ticket_id") or "ESC-NEW"
        reason = data.get("reason", "")
        if reason == "emergency":
            return (
                f"Your request has been escalated to our emergency response team (Ticket #{ticket_id}). "
                "Someone will contact you immediately.",
                conversation_id,
                ms,
            )
        # For non-emergency escalations, return None so server can answer via FAQ or guided help
        return None, conversation_id, ms

    response_text = (
        data.get("response")
        or data.get("answer")
        or data.get("text")
        or data.get("output")
    )

    msg_field = data.get("message")
    if msg_field:
        clean_msg = msg_field.strip().lower()
        clean_input = text.strip().lower()
        # NEVER return the user's question back to them
        if clean_msg != clean_input:
            if "please provide: all" in clean_msg:
                response_text = (
                    "I would be glad to help you book a table! Could you please let me know "
                    "what date, time, and how many guests will be in your party?"
                )
            elif not response_text:
                response_text = msg_field

    if not response_text:
        status = data.get("status", "")
        if status == "escalated":
            reason = data.get("reason", "")
            reason_map = {
                "low_confidence": "I didn't quite catch that",
                "unclear_intent": "I'm not sure what you'd like to do",
                "out_of_scope": "That's outside what I can help with",
                "no_match": "I couldn't find an answer for that",
            }
            prefix = reason_map.get(reason, "I'm not sure I understood")
        elif status == "confirmed":
            party = data.get("party_size", 2)
            d_val = data.get("date", "upcoming date")
            t_val = data.get("time", "your requested time")
            response_text = (
                f"Your reservation is confirmed! A table for {party} guests has been booked "
                f"for {d_val} at {t_val}. We look forward to hosting you!"
            )
        elif status == "need_more_info":
            response_text = data.get("message") or "Could you please provide the date, time, and number of guests?"

    return response_text, conversation_id, ms