"""Cartesia voice cloning — instant clone from a short clip.

The flow:
1. Caller uploads a 10–30s audio sample (mp3/wav) of the desired voice.
2. We POST it to Cartesia's `voices/clone/clip` endpoint.
3. Cartesia returns a `voice_id` we can immediately pass to the streaming TTS.

We also keep a small in-memory registry of personas (name → voice_id) so the
demo UI can let stakeholders A/B between a stock voice and one or more cloned
voices without restarting the bot.

For a production system, persist the registry in a DB and add per-tenant
access controls — voice clones are sensitive PII.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx
from loguru import logger

from .config import get_settings


CARTESIA_BASE = "https://api.cartesia.ai"
CARTESIA_VERSION = "2024-11-13"


class CartesiaError(RuntimeError):
    pass


@dataclass
class ClonedVoice:
    voice_id: str
    name: str
    description: str
    mode: str  # "stability" | "similarity"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PersonaRegistry:
    """In-memory registry of cloned voices keyed by short persona name."""

    voices: dict[str, ClonedVoice] = field(default_factory=dict)
    active_persona: Optional[str] = None

    def add(self, persona: str, voice: ClonedVoice) -> None:
        self.voices[persona] = voice
        if self.active_persona is None:
            self.active_persona = persona

    def remove(self, persona: str) -> None:
        self.voices.pop(persona, None)
        if self.active_persona == persona:
            self.active_persona = next(iter(self.voices), None)

    def active_voice_id(self) -> Optional[str]:
        if self.active_persona and self.active_persona in self.voices:
            return self.voices[self.active_persona].voice_id
        return None


REGISTRY = PersonaRegistry()


def resolve_voice_id() -> str:
    """Pick the voice id for the next TTS turn.

    Precedence: active cloned persona → env CARTESIA_CLONED_VOICE_ID → stock voice.
    """
    settings = get_settings()
    cloned = REGISTRY.active_voice_id() or settings.cartesia_cloned_voice_id
    return cloned or settings.cartesia_voice_id


async def clone_from_clip(
    *,
    audio_bytes: bytes,
    name: str,
    description: str = "",
    language: str = "en",
    mode: str = "stability",
) -> ClonedVoice:
    """Upload a clip and register the returned voice.

    `mode`:
      - "stability"  — closer to your sample (recommended for a single curated voice)
      - "similarity" — more expressive but may drift from the source voice
    """
    settings = get_settings()
    if not settings.cartesia_api_key:
        raise CartesiaError("CARTESIA_API_KEY is not configured")

    files = {
        "clip": ("clip.wav", io.BytesIO(audio_bytes), "audio/wav"),
    }
    data = {
        "name": name,
        "description": description,
        "language": language,
        "mode": mode,
        "enhance": "true",
    }
    headers = {
        "X-API-Key": settings.cartesia_api_key,
        "Cartesia-Version": CARTESIA_VERSION,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{CARTESIA_BASE}/voices/clone",
            headers=headers,
            data=data,
            files=files,
        )
    if r.status_code >= 400:
        logger.error(f"cartesia clone failed status={r.status_code} body={r.text}")
        raise CartesiaError(f"cartesia clone failed: {r.text}")

    body = r.json()
    voice_id = body.get("id") or body.get("voice_id")
    if not voice_id:
        raise CartesiaError(f"cartesia returned no voice id: {body}")

    return ClonedVoice(
        voice_id=voice_id,
        name=name,
        description=description,
        mode=mode,
    )


async def list_remote_voices() -> list[dict]:
    """Convenience pass-through to Cartesia's voice list — useful for the demo UI."""
    settings = get_settings()
    if not settings.cartesia_api_key:
        raise CartesiaError("CARTESIA_API_KEY is not configured")
    headers = {
        "X-API-Key": settings.cartesia_api_key,
        "Cartesia-Version": CARTESIA_VERSION,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{CARTESIA_BASE}/voices", headers=headers)
    r.raise_for_status()
    return r.json()
