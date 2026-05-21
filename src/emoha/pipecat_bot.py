"""Pipecat 1.2.1 WebRTC bot — Daily transport, Deepgram STT, Claude Sonnet 4.6, Cartesia TTS.

Latency budget:
- Deepgram streaming with utterance_end_ms=900 (elderly callers pause more)
- Claude streams tokens; Pipecat sentence-aggregates into TTS chunks
- Cartesia Sonic TTS streams audio with ~90ms TTFB
- Tools execute via FunctionCallParams; LLM streams its post-tool reply as it arrives,
  so the caller hears the answer while the side-effect is recorded.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import aiohttp
from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

from .transcript_broadcaster import TranscriptBroadcaster
from pipecat.services.anthropic.llm import AnthropicLLMService, AnthropicLLMSettings
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService, LiveOptions
from pipecat.transports.daily.transport import DailyParams, DailyTransport

from .cartesia_cloning import resolve_voice_id
from .config import get_settings
from .prompts import SYSTEM_PROMPT
from .state import STATE_STORE
from .tools import TOOLS, dispatch

try:
    from pipecat.services.tavus.video import TavusVideoService  # type: ignore
except ImportError:  # tavus extra not installed — pipeline runs audio-only
    TavusVideoService = None  # type: ignore


GREETING_DEFAULT = (
    "Hi, this is the Emoha care advisor. Thank you for calling. "
    "Take your time — what's been on your mind today about your parents?"
)


def _greeting_for(conversation_id: str) -> str:
    state = STATE_STORE.get(conversation_id)
    if not state:
        return GREETING_DEFAULT
    name = state.caller_name
    parent_word = "your parents"
    # We don't carry parent_relation in state, but if a caller name is present
    # the brief was likely submitted — give a softer, personalised opener.
    if name:
        return (
            f"Hi {name}. Thank you for taking the time to reach out. "
            f"Take a breath — there's no rush. Tell me, what's been on your mind?"
        )
    return GREETING_DEFAULT


def _system_prompt_with_brief(conversation_id: str) -> str:
    state = STATE_STORE.get(conversation_id)
    if not state:
        return SYSTEM_PROMPT
    bits = []
    if state.caller_name:
        bits.append(f"Caller's name: {state.caller_name}")
    p = state.parent
    if p.city:
        bits.append(f"Parent lives in: {p.city}")
    if p.lives_alone is not None:
        bits.append(f"Lives alone: {'yes' if p.lives_alone else 'no'}")
    if p.distance_from_family:
        bits.append(f"Caller's distance: {p.distance_from_family}")
    if p.mobility:
        bits.append(f"Mobility: {p.mobility}")
    if p.chronic_conditions:
        bits.append(f"Conditions mentioned: {', '.join(p.chronic_conditions)}")
    if state.risk.notes:
        bits.append("Caller's opening note: " + state.risk.notes[-1])
    if not bits:
        return SYSTEM_PROMPT
    brief_block = (
        "\n\n# What the caller already told us (do NOT re-ask these):\n"
        + "\n".join(f"- {b}" for b in bits)
        + "\nReference these naturally as if you remember them — never read them back as a list."
    )
    return SYSTEM_PROMPT + brief_block


def _build_tools_schema() -> ToolsSchema:
    """Convert our Anthropic-format TOOLS into pipecat's neutral schema."""
    fns = []
    for t in TOOLS:
        schema = t["input_schema"]
        fns.append(
            FunctionSchema(
                name=t["name"],
                description=t["description"],
                properties=schema.get("properties", {}),
                required=schema.get("required", []),
            )
        )
    return ToolsSchema(standard_tools=fns)


async def _register_tools(llm: AnthropicLLMService, conversation_id: str) -> None:
    """Wire every tool through pipecat's function-calling dispatch."""

    def make_handler(name: str):
        async def handler(params):  # type: ignore[no-untyped-def]
            args = params.arguments or {}
            logger.info(f"emoha tool_call cid={conversation_id[:8]} name={name} args={args}")
            result = await asyncio.to_thread(dispatch, name, conversation_id, args)
            logger.info(f"emoha tool_result cid={conversation_id[:8]} name={name} ok=True")
            await params.result_callback(result)

        return handler

    for tool in TOOLS:
        llm.register_function(tool["name"], make_handler(tool["name"]))


async def run_bot(
    room_url: str | None = None,
    token: str | None = None,
    conversation_id: str | None = None,
) -> None:
    settings = get_settings()
    conversation_id = conversation_id or str(uuid.uuid4())
    room_url = room_url or settings.daily_room_url
    if not room_url:
        raise RuntimeError("DAILY_ROOM_URL not configured")

    avatar_enabled = bool(
        TavusVideoService and settings.tavus_api_key and settings.tavus_replica_id
    )

    transport = DailyTransport(
        room_url,
        token,
        "Emoha Care Advisor",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_out_enabled=avatar_enabled,
            video_out_is_live=avatar_enabled,
            video_out_width=512 if avatar_enabled else 0,
            video_out_height=512 if avatar_enabled else 0,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    # Very aggressive turn-taking for the demo. Bump back
                    # toward 0.5-0.8 if elderly callers feel cut off mid-thought.
                    stop_secs=0.2,
                    start_secs=0.08,
                )
            ),
        ),
    )

    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        live_options=LiveOptions(
            model="nova-3",
            language="en",
            interim_results=True,
            # Deepgram requires this to be >= 1000ms. Elderly callers pause more,
            # so we sit at the floor — long enough to be patient, short enough
            # that the turn taker doesn't feel sluggish.
            utterance_end_ms=1000,
            smart_format=True,
            punctuate=True,
        ),
    )

    llm = AnthropicLLMService(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
        settings=AnthropicLLMSettings(
            # Haiku is plenty for 1–3 sentence empathic replies; a tighter cap
            # also nudges the model away from rambling continuations.
            max_tokens=512,
            enable_prompt_caching=True,
        ),
    )
    await _register_tools(llm, conversation_id)

    tts = CartesiaTTSService(
        api_key=settings.cartesia_api_key,
        voice_id=resolve_voice_id(),
        model="sonic-2",
        params=CartesiaTTSService.InputParams(
            language="en",
            speed="normal",
        ),
    )

    tools_schema = _build_tools_schema()
    context = LLMContext(
        messages=[{"role": "system", "content": _system_prompt_with_brief(conversation_id)}],
        tools=tools_schema,
    )
    aggregator = LLMContextAggregatorPair(context)

    avatar = None
    aio_session: aiohttp.ClientSession | None = None
    if avatar_enabled:
        aio_session = aiohttp.ClientSession()
        tavus_kwargs = {
            "api_key": settings.tavus_api_key,
            "replica_id": settings.tavus_replica_id,
            "session": aio_session,
        }
        if settings.tavus_persona_id:
            tavus_kwargs["persona_id"] = settings.tavus_persona_id
        avatar = TavusVideoService(**tavus_kwargs)
        logger.info(
            f"tavus avatar enabled replica={settings.tavus_replica_id} "
            f"persona={settings.tavus_persona_id or '<default>'}"
        )

    # Two broadcaster instances — one before the user aggregator (to catch
    # TranscriptionFrame, which the aggregator consumes), one after TTS (to
    # catch TTSTextFrame which TTS emits). Both push transport messages to
    # the browser via Daily's app-message channel.
    caller_broadcaster = TranscriptBroadcaster()
    bot_broadcaster = TranscriptBroadcaster()

    # Avatar processor sits between TTS and the transport output: it consumes the
    # audio frames TTS emits and produces lip-synced video frames Daily publishes.
    stages: list[Any] = [
        transport.input(),
        stt,
        caller_broadcaster,
        aggregator.user(),
        llm,
        tts,
        bot_broadcaster,
    ]
    if avatar:
        stages.append(avatar)
    stages.extend([transport.output(), aggregator.assistant()])

    pipeline = Pipeline(stages)

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
        ),
    )

    participant_joined = asyncio.Event()

    @transport.event_handler("on_first_participant_joined")
    async def on_join(transport, participant):  # type: ignore[no-untyped-def]
        # Speak the greeting directly. Avoids a first-token LLM round-trip
        # and lets the avatar start lip-syncing immediately.
        participant_joined.set()
        await task.queue_frames([TTSSpeakFrame(_greeting_for(conversation_id))])

    @transport.event_handler("on_participant_left")
    async def on_leave(transport, participant, reason):  # type: ignore[no-untyped-def]
        await task.queue_frame(EndFrame())

    async def _watchdog() -> None:
        """End the session if no one joins quickly, and hard-cap total runtime.

        Prevents zombie bots — without this, a session whose caller never joined
        keeps the pipeline (and any failing STT reconnect loops) running forever.
        """
        try:
            await asyncio.wait_for(participant_joined.wait(), timeout=180.0)
        except asyncio.TimeoutError:
            logger.warning(
                f"emoha bot {conversation_id}: no caller joined in 3 min, ending"
            )
            await task.queue_frame(EndFrame())
            return
        try:
            await asyncio.sleep(30 * 60)
            logger.warning(
                f"emoha bot {conversation_id}: 30-min session cap reached, ending"
            )
            await task.queue_frame(EndFrame())
        except asyncio.CancelledError:
            pass

    watchdog = asyncio.create_task(_watchdog())

    runner = PipelineRunner()
    logger.info(f"emoha pipecat bot starting conversation_id={conversation_id}")
    try:
        await runner.run(task)
    finally:
        watchdog.cancel()
        try:
            await watchdog
        except (asyncio.CancelledError, Exception):
            pass
        if aio_session is not None:
            await aio_session.close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--room", help="Daily room URL (overrides DAILY_ROOM_URL)")
    parser.add_argument("--token", help="Daily meeting token")
    args = parser.parse_args()

    asyncio.run(run_bot(room_url=args.room, token=args.token))


if __name__ == "__main__":
    main()
