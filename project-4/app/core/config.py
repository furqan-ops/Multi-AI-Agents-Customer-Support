import os
from pathlib import Path
from dotenv import load_dotenv

# Try loading .env from current directory, project root, or workspace root
for env_path in [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[3] / ".env",
]:
    if env_path.is_file():
        load_dotenv(env_path)
        break

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")

SUPERVISOR_URL = os.getenv("SUPERVISOR_URL", "http://localhost:5678/webhook/supervisor")

STT_MODEL = "nova-2"                              # Deepgram
TTS_VOICE = "en-US-AriaNeural"                    # edge-tts voice

def check_config() -> list[str]:
    missing = []
    if not DEEPGRAM_API_KEY: missing.append("DEEPGRAM_API_KEY")
    if not SUPABASE_URL: missing.append("SUPABASE_URL")
    if not SUPABASE_SECRET_KEY: missing.append("SUPABASE_SECRET_KEY")
    return missing