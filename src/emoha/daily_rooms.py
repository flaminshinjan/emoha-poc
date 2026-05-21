"""Daily room + meeting token helpers."""

from __future__ import annotations

import time
from typing import Optional

import httpx

from .config import get_settings


DAILY_API = "https://api.daily.co/v1"


class DailyError(RuntimeError):
    pass


async def create_room(
    name: Optional[str] = None,
    *,
    minutes: int = 60,
    enable_recording: bool = False,
) -> dict:
    settings = get_settings()
    if not settings.daily_api_key:
        raise DailyError("DAILY_API_KEY not configured")
    payload = {
        "properties": {
            "exp": int(time.time()) + minutes * 60,
            "eject_at_room_exp": True,
            "enable_chat": False,
            "enable_screenshare": False,
            "start_video_off": False,
            "start_audio_off": False,
            "enable_recording": "cloud" if enable_recording else False,
        }
    }
    if name:
        payload["name"] = name
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{DAILY_API}/rooms",
            headers={"Authorization": f"Bearer {settings.daily_api_key}"},
            json=payload,
        )
    if r.status_code >= 400:
        raise DailyError(f"daily create_room failed: {r.text}")
    return r.json()


async def mint_token(room_name: str, *, user_name: str, is_owner: bool = False) -> str:
    settings = get_settings()
    if not settings.daily_api_key:
        raise DailyError("DAILY_API_KEY not configured")
    payload = {
        "properties": {
            "room_name": room_name,
            "user_name": user_name,
            "is_owner": is_owner,
            "exp": int(time.time()) + 60 * 60,
        }
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{DAILY_API}/meeting-tokens",
            headers={"Authorization": f"Bearer {settings.daily_api_key}"},
            json=payload,
        )
    if r.status_code >= 400:
        raise DailyError(f"daily mint_token failed: {r.text}")
    return r.json()["token"]
