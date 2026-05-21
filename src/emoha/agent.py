"""Streaming Claude agent used by the FastAPI HTTP path and the Bland webhook.

The Pipecat voice path does NOT use this — it streams through Pipecat's
AnthropicLLMService directly so audio frames flow to TTS as the LLM emits
text. This module is for the non-WebRTC entry points (text chat, Bland turn
fulfillment) where we run a full tool-loop and return either streamed text
or a final string.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import (
    MessageParam,
    TextBlock,
    ToolUseBlock,
)

from .config import get_settings
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS, dispatch


class EmohaAgent:
    """One agent per process; cheap to instantiate but the Anthropic client is reusable."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        # History is kept by caller (conversation_id keyed) — agent is stateless across calls.

    async def stream_turn(
        self,
        *,
        conversation_id: str,
        history: list[MessageParam],
        user_text: str,
    ) -> AsyncIterator[str]:
        """Run one user turn through the agent, yielding spoken text deltas.

        Resolves tool calls in a loop, only yielding the final assistant text
        deltas (tool input deltas are suppressed — they are silent side-effects).
        Appends the final assistant message to `history` in place so the caller
        can persist it.
        """
        messages: list[MessageParam] = list(history) + [
            {"role": "user", "content": user_text}
        ]

        while True:
            stream = self._client.messages.stream(
                model=self._model,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                max_tokens=1024,
                messages=messages,
            )

            tool_uses: list[ToolUseBlock] = []
            text_blocks: list[TextBlock] = []

            async with stream as s:
                async for event in s:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield event.delta.text
                final = await s.get_final_message()

            for block in final.content:
                if block.type == "text":
                    text_blocks.append(block)
                elif block.type == "tool_use":
                    tool_uses.append(block)

            messages.append({"role": "assistant", "content": final.content})

            if final.stop_reason != "tool_use":
                # Persist the assistant turn back into the caller's history.
                history.append({"role": "user", "content": user_text})
                history.append({"role": "assistant", "content": final.content})
                return

            tool_results = []
            for tu in tool_uses:
                result = dispatch(tu.name, conversation_id, tu.input or {})
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": json.dumps(result),
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            # Loop back — Claude will produce the next text turn now that it has tool output.

    async def respond(
        self,
        *,
        conversation_id: str,
        history: list[MessageParam],
        user_text: str,
    ) -> str:
        """Non-streaming convenience wrapper — used by Bland's webhook, which expects a final string."""
        chunks: list[str] = []
        async for piece in self.stream_turn(
            conversation_id=conversation_id, history=history, user_text=user_text
        ):
            chunks.append(piece)
        return "".join(chunks).strip()


_AGENT: EmohaAgent | None = None


def get_agent() -> EmohaAgent:
    global _AGENT
    if _AGENT is None:
        _AGENT = EmohaAgent()
    return _AGENT
