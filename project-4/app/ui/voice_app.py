import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
import json
import uuid
from datetime import datetime
import streamlit as st
from audio_recorder_streamlit import audio_recorder

from app.core.config import (
    SUPERVISOR_URL, STT_MODEL, TTS_VOICE, check_config,
)
from app.core.voice_io import transcribe, synthesize, call_supervisor
from app.core.logger import log_voice_call

# ───────────────────────── Page Config ─────────────────────────
st.set_page_config(
    page_title="Voice Agent",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Modern Glassmorphic CSS ─────────────────────────
st.markdown("""
<style>
  * { 
    margin: 0; 
    padding: 0; 
    box-sizing: border-box;
  }
  
  /* Page background with gradient */
  .stApp {
    background: linear-gradient(135deg, #fef3e2 0%, #fce4ec 50%, #e3f2fd 100%);
    min-height: 100vh;
    color: #1a1f36;
  }
  
  /* Hide Streamlit chrome */
  #MainMenu, header, footer { visibility: hidden; }
  .stDeployButton { visibility: hidden; }
  .block-container { padding: 0 !important; }
  
  /* Main layout container */
  .main-wrapper {
    display: flex;
    min-height: 100vh;
    gap: 0;
  }
  
  /* ───── SIDEBAR STYLING ───── */
  section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.3);
    padding: 1.5rem !important;
    width: 280px;
    overflow-y: auto;
  }
  
  section[data-testid="stSidebar"]::-webkit-scrollbar {
    width: 6px;
  }
  
  section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background: rgba(200, 150, 200, 0.5);
    border-radius: 3px;
  }
  
  .sidebar-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1a1f36;
    margin-bottom: 1.5rem;
    letter-spacing: -0.3px;
  }
  
  .section-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: #d946a6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 1.2rem;
    margin-bottom: 0.6rem;
  }
  
  .metric-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    font-size: 0.8rem;
    color: #6b7280;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }
  
  .metric-value {
    font-family: 'Monaco', 'Courier New', monospace;
    color: #1a1f36;
    font-weight: 600;
    font-size: 0.75rem;
  }
  
  section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-top: 0.5rem;
  }
  
  section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(236, 72, 153, 0.3);
  }
  
  /* ───── CONTENT AREA ───── */
  .content-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: transparent;
    min-height: 100vh;
  }
  
  /* Main content padding */
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    overflow-y: auto;
  }
  
  .main-content::-webkit-scrollbar {
    width: 6px;
  }
  
  .main-content::-webkit-scrollbar-thumb {
    background: rgba(200, 150, 200, 0.3);
    border-radius: 3px;
  }
  
  /* ───── HEADER ───── */
  .header-section {
    text-align: center;
    margin-bottom: 2rem;
    animation: fadeInDown 0.6s ease;
  }
  
  .header-title {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
  }
  
  .header-subtitle {
    font-size: 0.9rem;
    color: #9ca3af;
    font-weight: 500;
  }
  
  /* ───── GLASSMORPHIC SPHERE ───── */
  .sphere-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 2rem 0;
    animation: fadeInUp 0.8s ease;
  }
  
  .sphere {
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.6) 0%, rgba(139, 92, 246, 0.6) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 2px solid rgba(255, 255, 255, 0.4);
    box-shadow: 
      0 8px 32px rgba(236, 72, 153, 0.2),
      inset -1px -1px 10px rgba(255, 255, 255, 0.4),
      inset 1px 1px 10px rgba(0, 0, 0, 0.1);
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
    transition: all 0.3s ease;
  }
  
  .sphere:hover {
    transform: scale(1.05);
    box-shadow: 
      0 12px 40px rgba(236, 72, 153, 0.3),
      inset -1px -1px 10px rgba(255, 255, 255, 0.5),
      inset 1px 1px 10px rgba(0, 0, 0, 0.15);
  }
  
  .sphere.recording {
    animation: pulse-glow 1.5s ease-in-out infinite;
  }
  
  .sphere-icon {
    font-size: 5rem;
    opacity: 0.8;
  }
  
  @keyframes pulse-glow {
    0%, 100% {
      box-shadow: 
        0 8px 32px rgba(236, 72, 153, 0.2),
        inset -1px -1px 10px rgba(255, 255, 255, 0.4),
        inset 1px 1px 10px rgba(0, 0, 0, 0.1);
    }
    50% {
      box-shadow: 
        0 16px 48px rgba(236, 72, 153, 0.4),
        inset -1px -1px 10px rgba(255, 255, 255, 0.5),
        inset 1px 1px 10px rgba(0, 0, 0, 0.15);
      transform: scale(1.08);
    }
  }
  
  @keyframes fadeInDown {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  /* ───── CHAT AREA ───── */
  .chat-container {
    width: 100%;
    max-width: 600px;
    margin: 1.5rem 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-height: 300px;
    overflow-y: auto;
    padding-right: 0.5rem;
  }
  
  .chat-container::-webkit-scrollbar {
    width: 6px;
  }
  
  .chat-container::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .chat-container::-webkit-scrollbar-thumb {
    background: rgba(236, 72, 153, 0.3);
    border-radius: 3px;
  }
  
  .message-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    animation: fadeInUp 0.4s ease;
  }
  
  .message-group.user {
    align-items: flex-end;
  }
  
  .message-group.agent {
    align-items: flex-start;
  }
  
  .message-bubble {
    max-width: 85%;
    padding: 0.85rem 1.1rem;
    border-radius: 16px;
    font-size: 0.9rem;
    line-height: 1.5;
    word-wrap: break-word;
    animation: slideIn 0.3s ease;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .message-bubble.user {
    background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
    color: white;
    border-radius: 18px 18px 4px 18px;
    box-shadow: 0 2px 8px rgba(236, 72, 153, 0.2);
  }
  
  .message-bubble.agent {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    color: #1a1f36;
    border-radius: 18px 18px 18px 4px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  
  .message-bubble.error {
    background: rgba(239, 68, 68, 0.1);
    color: #991b1b;
    border-radius: 12px;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  
  .message-time {
    font-size: 0.7rem;
    opacity: 0.6;
    margin-top: 0.2rem;
    color: #6b7280;
  }
  
  .message-metrics {
    font-size: 0.65rem;
    opacity: 0.5;
    margin-top: 0.3rem;
    color: #9ca3af;
  }
  
  /* ───── INPUT AREA ───── */
  .input-section {
    width: 100%;
    max-width: 600px;
    padding: 2rem 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }
  
  .input-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .voice-recorder-wrapper {
    display: flex;
    justify-content: center;
    width: 100%;
  }
  
  .voice-recorder-wrapper > div {
    display: flex;
    justify-content: center;
  }
  
  .success-message {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    color: #065f46;
    font-size: 0.85rem;
    font-weight: 500;
    animation: fadeInDown 0.3s ease;
  }
  
  /* ───── BUTTONS ───── */
  .stButton > button {
    background: linear-gradient(135deg, #ec4899 0%, #db2777 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
  }
  
  .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 16px rgba(236, 72, 153, 0.3) !important;
  }
  
  /* ───── AUDIO PLAYER STYLING ───── */
  audio {
    width: 100% !important;
    max-width: 500px !important;
    height: 44px !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, rgba(236, 72, 153, 0.1) 100%) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(236, 72, 153, 0.3) !important;
    padding: 0.5rem !important;
    box-shadow: 0 4px 12px rgba(236, 72, 153, 0.15) !important;
  }
  
  audio::-webkit-media-controls-panel {
    background-color: transparent !important;
  }
  
  audio::-webkit-media-controls-mute-button {
    filter: invert(0.7);
  }
  
  audio::-webkit-media-controls-play-button {
    filter: invert(0.7);
  }
  
  audio::-webkit-media-controls-timeline {
    background: rgba(236, 72, 153, 0.2) !important;
    border-radius: 4px !important;
  }
  
  /* ───── SENDING STATE ───── */
  .sending-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #ec4899;
    font-weight: 600;
    margin: 1rem 0;
    animation: fadeInDown 0.3s ease;
  }
  
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(236, 72, 153, 0.3);
    border-top-color: #ec4899;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  
  /* ───── RESPONSIVE DESIGN ───── */
  @media (max-width: 1024px) {
    section[data-testid="stSidebar"] {
      width: 240px;
      padding: 1rem !important;
    }
    
    .header-title {
      font-size: 1.6rem;
    }
    
    .sphere {
      width: 240px;
      height: 240px;
    }
    
    .sphere-icon {
      font-size: 4rem;
    }
    
    .main-content {
      padding: 1.5rem;
    }
  }
  
  @media (max-width: 768px) {
    .main-wrapper {
      flex-direction: column;
    }
    
    section[data-testid="stSidebar"] {
      width: 100%;
      max-height: 120px;
      overflow-x: auto;
      overflow-y: hidden;
      padding: 1rem !important;
      border-right: none;
      border-bottom: 1px solid rgba(255, 255, 255, 0.3);
      display: flex;
      gap: 2rem;
      align-items: center;
    }
    
    .sidebar-title {
      margin-bottom: 0;
      white-space: nowrap;
    }
    
    .section-title,
    .metric-row {
      display: none;
    }
    
    .stApp {
      background: linear-gradient(135deg, #fef3e2 0%, #fce4ec 50%, #e3f2fd 100%);
    }
    
    .header-title {
      font-size: 1.4rem;
    }
    
    .sphere {
      width: 200px;
      height: 200px;
    }
    
    .sphere-icon {
      font-size: 3rem;
    }
    
    .main-content {
      padding: 1rem;
    }
    
    .chat-container {
      max-width: 100%;
      max-height: 200px;
    }
    
    .message-bubble {
      max-width: 90%;
    }
    
    .input-section {
      max-width: 100%;
    }
    
    .header-subtitle {
      font-size: 0.8rem;
    }
  }
  
  @media (max-width: 480px) {
    .header-title {
      font-size: 1.2rem;
    }
    
    .sphere {
      width: 160px;
      height: 160px;
    }
    
    .sphere-icon {
      font-size: 2.5rem;
    }
    
    .chat-container {
      max-height: 150px;
    }
    
    .message-bubble {
      font-size: 0.85rem;
      padding: 0.7rem 0.9rem;
    }
    
    .main-content {
      padding: 0.75rem;
    }
  }
  
  /* ───── EMPTY STATE ───── */
  .empty-state {
    text-align: center;
    color: #9ca3af;
    font-size: 0.9rem;
    opacity: 0.8;
  }
  
</style>
""", unsafe_allow_html=True)

# ───────────────────────── Config Check ─────────────────────────
missing = check_config()
if missing:
    st.error(f"Missing in .env: {', '.join(missing)}")
    st.stop()

# ───────────────────────── Session State ─────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "played_turns" not in st.session_state:
    st.session_state.played_turns = set()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "session_start" not in st.session_state:
    st.session_state.session_start = time.time()
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🎤 Voice Agent</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Session Info</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-row"><span>ID</span><span class="metric-value">{st.session_state.session_id}</span></div>', unsafe_allow_html=True)
    
    uptime_sec = int(time.time() - st.session_state.session_start)
    uptime_str = f"{uptime_sec // 60}m" if uptime_sec >= 60 else f"{uptime_sec}s"
    st.markdown(f'<div class="metric-row"><span>Uptime</span><span class="metric-value">{uptime_str}</span></div>', unsafe_allow_html=True)
    
    # Metrics
    completed = [t for t in st.session_state.history if t.get("result") and not t["result"].get("error")]
    
    if completed:
        st.markdown('<div class="section-title">Performance</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Turns</span><span class="metric-value">{len(completed)}</span></div>', unsafe_allow_html=True)
        
        stt_list = [t["result"]["stt_ms"] for t in completed]
        sup_list = [t["result"]["sup_ms"] for t in completed]
        tts_list = [t["result"]["tts_ms"] for t in completed]
        
        st.markdown(f'<div class="metric-row"><span>STT avg</span><span class="metric-value">{sum(stt_list)/len(stt_list):.0f}ms</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Sup avg</span><span class="metric-value">{sum(sup_list)/len(sup_list):.0f}ms</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>TTS avg</span><span class="metric-value">{sum(tts_list)/len(tts_list):.0f}ms</span></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin: 1.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);"></div>', unsafe_allow_html=True)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.played_turns = set()
        st.session_state.session_start = time.time()
        st.rerun()

# ───────────────────────── Main Content ─────────────────────────
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-section">
  <div class="header-title">Voice Agent</div>
  <div class="header-subtitle">Speak naturally, AI responds instantly</div>
</div>
""", unsafe_allow_html=True)

# Sphere
st.markdown(f"""
<div class="sphere-container">
  <div class="sphere {'recording' if st.session_state.is_recording else ''}">
    <div class="sphere-icon">🎤</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Chat History
if st.session_state.history:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for i, turn in enumerate(st.session_state.history):
        if turn["role"] != "user_audio" or "result" not in turn:
            continue
        
        r = turn["result"]
        ts = datetime.now().strftime("%H:%M")
        
        if r.get("error"):
            st.markdown(f"""
            <div class="message-group user">
              <div class="message-bubble error">❌ Recording failed</div>
            </div>
            """, unsafe_allow_html=True)
            continue
        
        user_text = (r.get("text") or "").strip() or "(silent)"
        agent_text = (r.get("resp_text") or "").strip() or "(no response)"
        
        # User message
        st.markdown(f"""
        <div class="message-group user">
          <div class="message-bubble user">{user_text}</div>
          <div class="message-time">{ts}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Agent message
        st.markdown(f"""
        <div class="message-group agent">
          <div class="message-bubble agent">{agent_text}</div>
          <div class="message-time">{ts}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio playback
        if r.get("audio_out"):
            is_last = (i == len(st.session_state.history) - 1)
            should_autoplay = is_last and (i not in st.session_state.played_turns)
            st.audio(r["audio_out"], format="audio/mp3", autoplay=should_autoplay)
            if should_autoplay:
                st.session_state.played_turns.add(i)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Input Section
st.markdown('<div class="input-section">', unsafe_allow_html=True)
st.markdown('<div class="input-label">🎙️ Press to record</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ec4899",
        neutral_color="#8b5cf6",
        icon_name="microphone",
        icon_size="3x",
        pause_threshold=6.0,
        sample_rate=16000,
        key="voice_recorder",
    )

if audio_bytes:
    st.markdown(f'<div class="success-message">✓ Recorded {len(audio_bytes) / 1024:.1f} KB</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📤 Send", type="primary", use_container_width=True):
            if len(audio_bytes) > 960_000:
                st.error("⚠️ Recording too long (>30s). Please record a shorter message.")
            else:
                st.session_state.history.append({"role": "user_audio", "bytes": audio_bytes})
                st.markdown('<div class="sending-indicator"><span class="spinner"></span> Processing your message...</div>', unsafe_allow_html=True)
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# ───────────────────────── Pipeline ─────────────────────────
for i, turn in enumerate(st.session_state.history):
    if turn["role"] != "user_audio" or "result" in turn:
        continue

    # Show processing indicator
    processing_placeholder = st.empty()
    processing_placeholder.markdown(
        '<div class="sending-indicator"><span class="spinner"></span> Processing your message...</div>',
        unsafe_allow_html=True
    )

    print(f"\n🔵 Processing turn {i+1}...")
    print(f"   Audio bytes: {len(turn.get('bytes', b''))} bytes")

    try:
        print(f"   → Transcribing audio...")
        text, stt_ms = transcribe(turn["bytes"], "audio/wav")
        print(f"   ✓ STT result: '{text}' ({stt_ms}ms)")
    except Exception as e:
        print(f"   ✗ STT ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        turn["result"] = {"error": f"STT failed: {str(e)[:100]}"}
        st.rerun()

    try:
        print(f"   → Calling supervisor...")
        resp_text, cid, sup_ms = call_supervisor(text)
        print(f"   ✓ Supervisor result: '{resp_text}' ({sup_ms}ms)")
    except Exception as e:
        print(f"   ✗ SUPERVISOR ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        turn["result"] = {"error": f"Supervisor failed: {str(e)[:100]}", "text": text, "stt_ms": stt_ms}
        st.rerun()

    tts_error = None
    try:
        print(f"   → Synthesizing speech...")
        audio_out, tts_ms = synthesize(resp_text)
        print(f"   ✓ TTS result: {len(audio_out)} bytes ({tts_ms}ms)")
    except Exception as e:
        print(f"   ⚠ TTS ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        tts_error = str(e)
        audio_out, tts_ms = b"", 0

    total_ms = stt_ms + sup_ms + tts_ms
    turn["result"] = {
        "text": text,
        "stt_ms": stt_ms,
        "resp_text": resp_text,
        "cid": cid,
        "sup_ms": sup_ms,
        "audio_out": audio_out,
        "tts_ms": tts_ms,
        "tts_error": tts_error,
        "total_ms": total_ms,
    }

    try:
        log_voice_call(
            conversation_id=cid or f"voice-{st.session_state.session_id}-t{i+1}",
            transcript=text,
            response_text=resp_text,
            stt_model=STT_MODEL,
            tts_model="edge-tts",
            tts_voice=TTS_VOICE,
            stt_latency_ms=stt_ms,
            supervisor_latency_ms=sup_ms,
            tts_latency_ms=tts_ms,
            total_latency_ms=total_ms,
            status="tts_failed" if tts_error else "ok",
            error=tts_error,
        )
        print(f"✓ Logged to database")
    except Exception as e:
        print(f"⚠ Logging error: {e}")

    print(f"🟢 Turn {i+1} complete\n")
    processing_placeholder.empty()
    st.rerun()