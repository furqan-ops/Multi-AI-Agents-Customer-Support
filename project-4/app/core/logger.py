from datetime import datetime, timezone
from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_SECRET_KEY

_client: Client | None = None

def _sb() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return _client

def log_voice_call(
    *,
    conversation_id: str | None,
    transcript: str,
    response_text: str,
    stt_model: str,
    tts_model: str,
    tts_voice: str,
    audio_duration_sec: float | None = None,
    stt_latency_ms: int | None = None,
    supervisor_latency_ms: int | None = None,
    tts_latency_ms: int | None = None,
    total_latency_ms: int | None = None,
    status: str = "ok",
    error: str | None = None,
) -> dict | None:
    row = {
        "conversation_id": conversation_id,
        "transcript": transcript,
        "response_text": response_text,
        "stt_model": stt_model,
        "tts_model": tts_model,
        "tts_voice": tts_voice,
        "audio_duration_sec": audio_duration_sec,
        "stt_latency_ms": stt_latency_ms,
        "supervisor_latency_ms": supervisor_latency_ms,
        "tts_latency_ms": tts_latency_ms,
        "total_latency_ms": total_latency_ms,
        "status": status,
        "error": error,
    }
    try:
        res = _sb().table("voice_calls").insert(row).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"[logger] insert failed: {e}")
        return None