"""Bland.ai integration — outbound dial + per-turn webhook fulfillment.

Bland gives us two integration shapes:

1. Pathways with HTTP nodes — visual flow, fast, but constrains the LLM.
2. "Custom LLM" prompts plus webhook tools — Bland speaks, our agent thinks.

We use shape #2 here. Bland POSTs to /bland/turn on every caller utterance,
we run the Claude agent (with the full Emoha tool loop), and return the
spoken text Bland should say next.

The history is keyed by Bland's `call_id`. State lives in-process; for
production swap for Redis or the same store Pipecat uses.
"""

from __future__ import annotations

from typing import Any

import httpx
from anthropic.types import MessageParam
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from .agent import get_agent
from .care_summary import build_summary
from .config import get_settings
from .state import STATE_STORE


router = APIRouter(prefix="/bland", tags=["bland"])


# ---------- per-call history store ----------

_HISTORY: dict[str, list[MessageParam]] = {}


def _history(call_id: str) -> list[MessageParam]:
    return _HISTORY.setdefault(call_id, [])


# ---------- webhook payloads (Bland's request shapes) ----------


class BlandTurnRequest(BaseModel):
    """Bland posts this on every caller turn when configured with a webhook prompt."""

    call_id: str = Field(..., description="Bland's unique id for this call")
    transcript: str = Field(..., description="What the caller just said")
    metadata: dict[str, Any] | None = None


class BlandTurnResponse(BaseModel):
    response: str
    end_call: bool = False


@router.post("/turn", response_model=BlandTurnResponse)
async def bland_turn(req: BlandTurnRequest) -> BlandTurnResponse:
    """Single webhook Bland hits per caller utterance. Returns text to speak."""
    agent = get_agent()
    history = _history(req.call_id)
    spoken = await agent.respond(
        conversation_id=req.call_id,
        history=history,
        user_text=req.transcript,
    )
    state = STATE_STORE.get(req.call_id)
    end_call = bool(state and state.callback_scheduled and state.stage.value == "handoff")
    return BlandTurnResponse(response=spoken, end_call=end_call)


class BlandCallEndedRequest(BaseModel):
    call_id: str
    duration_seconds: int | None = None
    transcripts: list[dict[str, Any]] | None = None


@router.post("/call-ended")
async def bland_call_ended(req: BlandCallEndedRequest) -> dict[str, Any]:
    """Fire-and-forget hook so we can finalise the care summary."""
    state = STATE_STORE.get(req.call_id)
    if not state:
        return {"ok": True, "note": "no state for call"}
    summary = build_summary(state)
    logger.info(f"emoha bland call ended call_id={req.call_id} summary={summary}")
    return {"ok": True, "summary": summary}


# ---------- outbound dial ----------


class OutboundCallRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 destination number")
    caller_name: str | None = None
    first_message: str | None = None


@router.post("/outbound")
async def outbound_call(req: OutboundCallRequest) -> dict[str, Any]:
    """Trigger an outbound Bland call that uses our /bland/turn webhook as its brain."""
    settings = get_settings()
    if not settings.bland_api_key:
        raise HTTPException(500, "BLAND_API_KEY not configured")
    if not settings.bland_webhook_base:
        raise HTTPException(500, "BLAND_WEBHOOK_BASE not configured")

    payload = {
        "phone_number": req.phone_number,
        "from": settings.bland_phone_number,
        "task": (
            "You are speaking on behalf of Emoha Elder Care. For every caller utterance, "
            "POST the transcript to the webhook below and speak the response field. "
            "Match the caller's pace. Do not improvise — use only what the webhook returns."
        ),
        "first_sentence": req.first_message
        or "Hi, this is the Emoha care advisor. Is this a good time to talk?",
        "voice": "maya",  # warm female; swap if Emoha picks a different Bland voice
        "wait_for_greeting": True,
        "interruption_threshold": 120,
        "model": "enhanced",
        "language": "ENG",
        "webhook": f"{settings.bland_webhook_base.rstrip('/')}/bland/call-ended",
        "metadata": {"caller_name": req.caller_name} if req.caller_name else None,
        # Bland's "tools" array routes per-turn brain to our /bland/turn.
        "tools": [
            {
                "name": "emoha_brain",
                "description": "Get the next thing to say from Emoha's care advisor agent.",
                "url": f"{settings.bland_webhook_base.rstrip('/')}/bland/turn",
                "method": "POST",
                "body": {
                    "call_id": "{{call_id}}",
                    "transcript": "{{input.transcript}}",
                },
                "response": {
                    "response": "$.response",
                    "end_call": "$.end_call",
                },
                "speech": "$.response",
                "run_on_every_turn": True,
            }
        ],
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            "https://api.bland.ai/v1/calls",
            headers={"Authorization": settings.bland_api_key},
            json=payload,
        )
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()
