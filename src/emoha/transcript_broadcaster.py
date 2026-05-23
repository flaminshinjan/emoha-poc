"""Tiny pipeline processor that mirrors STT + TTS text into the Daily room as
app-messages so the browser can render a live transcript.

Why not RTVI? RTVIObserver needs an RTVIProcessor reference to actually send
messages — without it the events are silently dropped. This processor sidesteps
RTVI entirely and uses the standard `OutputTransportMessageFrame`, which the
DailyTransport publishes via Daily's `appMessage` channel.

Browser side: `call.on('app-message', e => ...)` and check `e.data.label === 'emoha-transcript'`.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from pipecat.frames.frames import (
    BotStoppedSpeakingFrame,
    Frame,
    LLMFullResponseEndFrame,
    OutputTransportMessageFrame,
    TranscriptionFrame,
    TTSTextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


_LABEL = "emoha-transcript"


class TranscriptBroadcaster(FrameProcessor):
    """Watches frames flowing through the pipeline and emits transport messages
    when caller speech is transcribed or the bot speaks.

    NOTE on placement:
        `TranscriptionFrame` is emitted by STT and is **consumed by the user
        context aggregator** that sits between STT and the LLM. A broadcaster
        placed downstream of that aggregator will never see caller speech.
        To capture both sides of the conversation we instantiate two
        broadcasters in the pipeline:

          stt → TranscriptBroadcaster (caller side: TranscriptionFrame)
              → aggregator.user() → llm → tts
              → TranscriptBroadcaster (bot side: TTSTextFrame)
              → transport.output()
    """

    def __init__(self, conversation_id: str | None = None) -> None:
        super().__init__()
        self._conversation_id = conversation_id
        # TTS in pipecat 1.x emits a TTSTextFrame *per token*, so naively
        # broadcasting each one produces word-soup. We buffer the bot's
        # tokens and flush as one line on the next BotStoppedSpeakingFrame
        # or LLMFullResponseEndFrame — whichever lands first.
        self._bot_buffer: list[str] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # `TranscriptionFrame` is the finalized transcript; the interim is
        # `InterimTranscriptionFrame`. Trust the type.
        if isinstance(frame, TranscriptionFrame):
            text = (frame.text or "").strip()
            if text:
                await self._broadcast({"role": "caller", "text": text})
                self._persist("caller", text)

        elif isinstance(frame, TTSTextFrame):
            chunk = (frame.text or "").strip()
            if chunk:
                self._bot_buffer.append(chunk)

        elif isinstance(frame, (BotStoppedSpeakingFrame, LLMFullResponseEndFrame)):
            await self._flush_bot_buffer()

        # Always forward — we're a passive observer, not a gate.
        await self.push_frame(frame, direction)

    async def _flush_bot_buffer(self) -> None:
        if not self._bot_buffer:
            return
        line = " ".join(self._bot_buffer).strip()
        # Tidy doubled spaces / spaces before punctuation that arise from
        # tokenwise concatenation.
        import re
        line = re.sub(r"\s+([.,!?;:])", r"\1", line)
        line = re.sub(r"\s+", " ", line)
        self._bot_buffer.clear()
        if line:
            await self._broadcast({"role": "advisor", "text": line})
            self._persist("advisor", line)

    def _persist(self, role: str, text: str) -> None:
        if not self._conversation_id:
            return
        try:
            from . import db
            if db.is_enabled():
                db.fire_and_forget(db.insert_transcript(self._conversation_id, role, text))
        except Exception:
            logger.exception("transcript persist failed")

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        message = {"label": _LABEL, **payload}
        try:
            await self.push_frame(
                OutputTransportMessageFrame(message=message),
                FrameDirection.DOWNSTREAM,
            )
        except Exception:
            logger.exception("transcript broadcast failed")
