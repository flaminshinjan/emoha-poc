"""FastAPI app — exposes:

- POST /chat            text chat with streaming SSE deltas (mirrors voice agent's brain)
- POST /chat/once       text chat returning a single string (handy for smoke tests)
- POST /pipecat/connect spawn a Pipecat bot into a Daily room and return join info
- POST /avatar/session  one-call demo bootstrap — creates a Daily room, spawns the
                        avatar bot, and returns join info for the browser
- POST /voice/clone     upload an audio clip and register a cloned Cartesia voice
- GET  /voice/list      list registered cloned voices (in-memory)
- POST /voice/select    set the active cloned persona for the next session
- POST /bland/outbound  fire an outbound Bland call (wired in bland_integration)
- POST /bland/turn      per-turn webhook for Bland (wired in bland_integration)
- POST /bland/call-ended finalisation webhook
- GET  /state/{cid}     debug — current ConversationState as JSON
- GET  /summary/{cid}   final care summary
- GET  /healthz
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional

from anthropic.types import MessageParam
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel, Field

from .agent import get_agent
from .bland_integration import router as bland_router
from .care_summary import build_summary
from .cartesia_cloning import REGISTRY, clone_from_clip
from .config import get_settings
from .daily_rooms import create_room, mint_token
from .state import STATE_STORE


app = FastAPI(title="Emoha Voice AI Care Advisor")
app.include_router(bland_router)

# Serve the standalone demo UI at /demo/* if the directory exists.
_web_dir = Path(__file__).resolve().parents[2] / "web"
if _web_dir.exists():
    app.mount("/demo", StaticFiles(directory=_web_dir, html=True), name="demo")


# --- in-process text chat history (parallel to Bland's per-call store) ---
_CHAT_HISTORY: dict[str, list[MessageParam]] = {}


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    user_text: str = Field(..., min_length=1)


@app.post("/chat")
async def chat(req: ChatRequest):
    """Stream the agent's spoken reply as Server-Sent Events.

    Each `data:` line is a token-ish text delta; a final `event: done` marks completion.
    Frontends and the Pipecat bot do not consume this endpoint — this is for HTTP tests
    and any text-only surface (e.g. a fallback chat widget).
    """
    cid = req.conversation_id or str(uuid.uuid4())
    history = _CHAT_HISTORY.setdefault(cid, [])
    agent = get_agent()

    async def event_stream():
        yield f"event: conversation_id\ndata: {cid}\n\n"
        try:
            async for piece in agent.stream_turn(
                conversation_id=cid, history=history, user_text=req.user_text
            ):
                yield f"data: {json.dumps(piece)}\n\n"
        except Exception as e:
            logger.exception("agent stream failed")
            yield f"event: error\ndata: {json.dumps(str(e))}\n\n"
            return
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat/once")
async def chat_once(req: ChatRequest):
    cid = req.conversation_id or str(uuid.uuid4())
    history = _CHAT_HISTORY.setdefault(cid, [])
    agent = get_agent()
    text = await agent.respond(
        conversation_id=cid, history=history, user_text=req.user_text
    )
    return {"conversation_id": cid, "response": text}


class PipecatConnectRequest(BaseModel):
    room_url: str | None = None
    token: str | None = None


@app.post("/pipecat/connect")
async def pipecat_connect(req: PipecatConnectRequest):
    """Spawn a Pipecat bot in the background that joins the given Daily room.

    For real deployments you would run pipecat workers in their own process/container
    and use a job queue. This shortcut is fine for demos.
    """
    from .pipecat_bot import run_bot

    settings = get_settings()
    room_url = req.room_url or settings.daily_room_url
    if not room_url:
        raise HTTPException(500, "DAILY_ROOM_URL not configured and none provided")

    asyncio.create_task(run_bot(room_url=room_url, token=req.token))
    return {"ok": True, "room_url": room_url}


# --- avatar session bootstrap ---


class BriefPrefill(BaseModel):
    """Data captured from the multi-step intake form before the call starts."""

    caller_name: Optional[str] = None
    parent_name: Optional[str] = None
    parent_relation: Optional[str] = None  # "mother" | "father" | "both"
    city: Optional[str] = None
    lives_alone: Optional[bool] = None
    distance: Optional[str] = None  # "same_city" | "different_city" | "abroad"
    mobility: Optional[str] = None  # "full" | "partial" | "limited"
    conditions: list[str] = []
    prompt: Optional[str] = None


class AvatarSessionRequest(BaseModel):
    advisor_slug: Optional[str] = None
    brief: Optional[BriefPrefill] = None


class AvatarSessionResponse(BaseModel):
    conversation_id: str
    room_url: str
    user_token: str
    avatar_enabled: bool
    active_voice_persona: Optional[str]


@app.post("/avatar/session", response_model=AvatarSessionResponse)
async def avatar_session(req: AvatarSessionRequest | None = None):
    """One call from the browser:

    1. Create a fresh Daily room (so each demo gets a clean slate).
    2. Mint a meeting token for the human caller AND a separate owner token for the bot.
    3. Optionally seed the conversation state with the intake brief.
    4. Spawn the Pipecat avatar bot in the background to join the room.
    5. Return the room URL + caller token — the browser joins with these.
    """
    settings = get_settings()
    if not settings.daily_api_key:
        raise HTTPException(500, "DAILY_API_KEY not configured")

    cid = str(uuid.uuid4())
    room = await create_room(name=f"emoha-{cid[:8]}", minutes=30)
    room_url: str = room["url"]
    room_name: str = room["name"]

    if req and req.advisor_slug and req.advisor_slug in REGISTRY.voices:
        # Caller picked a persona that has a cloned voice — use it for this session.
        REGISTRY.active_persona = req.advisor_slug

    # Seed state with the brief so the agent doesn't have to re-ask everything.
    state = STATE_STORE.get_or_create(cid)
    if req and req.brief:
        b = req.brief
        state.caller_name = b.caller_name
        if b.city:
            state.parent.city = b.city
        if b.lives_alone is not None:
            state.parent.lives_alone = b.lives_alone
        if b.distance:
            state.parent.distance_from_family = b.distance
        if b.mobility:
            state.parent.mobility = b.mobility
        if b.conditions:
            state.parent.chronic_conditions = [
                c for c in b.conditions if c != "None right now"
            ]
        if b.prompt:
            state.risk.notes.append(f"caller's opening note: {b.prompt}")

    bot_token = await mint_token(room_name, user_name="Emoha Care Advisor", is_owner=True)
    user_token = await mint_token(room_name, user_name="Caller", is_owner=False)

    from .pipecat_bot import run_bot

    asyncio.create_task(run_bot(room_url=room_url, token=bot_token, conversation_id=cid))

    avatar_enabled = bool(settings.tavus_api_key and settings.tavus_replica_id)
    return AvatarSessionResponse(
        conversation_id=cid,
        room_url=room_url,
        user_token=user_token,
        avatar_enabled=avatar_enabled,
        active_voice_persona=REGISTRY.active_persona,
    )


# --- voice cloning ---


class VoiceListItem(BaseModel):
    persona: str
    voice_id: str
    name: str
    description: str
    mode: str
    active: bool


@app.get("/voice/list", response_model=list[VoiceListItem])
async def voice_list():
    return [
        VoiceListItem(
            persona=persona,
            voice_id=v.voice_id,
            name=v.name,
            description=v.description,
            mode=v.mode,
            active=(REGISTRY.active_persona == persona),
        )
        for persona, v in REGISTRY.voices.items()
    ]


@app.post("/voice/clone")
async def voice_clone(
    persona: str = Form(..., description="Short slug to refer to this voice later"),
    name: str = Form(...),
    description: str = Form(""),
    mode: str = Form("stability"),
    clip: UploadFile = File(..., description="10–30s audio sample (wav/mp3/m4a)"),
):
    from .cartesia_cloning import CartesiaError

    audio_bytes = await clip.read()
    if not audio_bytes:
        raise HTTPException(400, "empty audio upload")
    try:
        voice = await clone_from_clip(
            audio_bytes=audio_bytes,
            name=name,
            description=description,
            mode=mode,
        )
    except CartesiaError as e:
        # Surface the actual Cartesia error to the client so the user sees
        # the real reason — usually "Feature not available on the free tier",
        # an over-quota notice, or an invalid clip. Status 402 maps naturally
        # to subscription/billing issues; 400 for everything else.
        msg = str(e)
        status = 402 if "subscription" in msg.lower() or "free tier" in msg.lower() else 400
        # Strip the "cartesia clone failed: " prefix we added in the lib.
        clean = msg.replace("cartesia clone failed: ", "").strip()
        raise HTTPException(status, clean)
    REGISTRY.add(persona, voice)
    logger.info(f"voice cloned persona={persona} voice_id={voice.voice_id}")
    return {
        "persona": persona,
        "voice_id": voice.voice_id,
        "active": REGISTRY.active_persona == persona,
    }


class VoiceSelectRequest(BaseModel):
    persona: str


@app.post("/voice/select")
async def voice_select(req: VoiceSelectRequest):
    if req.persona not in REGISTRY.voices:
        raise HTTPException(404, f"unknown persona {req.persona}")
    REGISTRY.active_persona = req.persona
    return {"active_persona": REGISTRY.active_persona}


@app.delete("/voice/{persona}")
async def voice_delete(persona: str):
    REGISTRY.remove(persona)
    return {"ok": True, "active_persona": REGISTRY.active_persona}


@app.get("/state/{conversation_id}")
async def get_state(conversation_id: str):
    state = STATE_STORE.get(conversation_id)
    if not state:
        raise HTTPException(404, "unknown conversation")
    return state.to_dict()


@app.get("/summary/{conversation_id}")
async def get_summary(conversation_id: str):
    state = STATE_STORE.get(conversation_id)
    if not state:
        raise HTTPException(404, "unknown conversation")
    return build_summary(state)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "emoha.server:app",
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
