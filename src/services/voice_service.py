import os
import base64
from typing import Tuple

import requests


ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_TTS_VOICE_ID = os.getenv("ELEVEN_TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")


def _headers() -> dict:
    return {"xi-api-key": ELEVEN_API_KEY}


def speech_to_text(audio_bytes: bytes, model: str = "default") -> str:
    """Send audio to ElevenLabs STT. Returns transcript text. Fallback: empty string."""
    if not ELEVEN_API_KEY:
        return ""
    url = "https://api.elevenlabs.io/v1/speech-to-text"
    files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
    data = {"model": model}
    try:
        resp = requests.post(url, headers=_headers(), files=files, data=data, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", "")
    except Exception:
        return ""


def text_to_speech(text: str, voice_id: str | None = None) -> bytes:
    """Generate spoken feedback from text via ElevenLabs TTS. Returns audio bytes (mp3)."""
    if not ELEVEN_API_KEY:
        return b""
    vid = voice_id or ELEVEN_TTS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    payload = {"text": text[:4000]}
    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=120)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return b""


