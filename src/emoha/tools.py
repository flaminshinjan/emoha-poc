"""Tool definitions for the agent.

Schemas are written in Anthropic's tool format. The same `TOOLS` list is
re-used by the Pipecat bot (Pipecat accepts Anthropic schemas natively when
using AnthropicLLMService).

Handlers operate on a ConversationState pulled from STATE_STORE. They are
intentionally fast and pure — no network — so they don't add latency to the
streaming TTS path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from .care_summary import build_summary, urgency_from_signals
from .knowledge import PLANS, SERVICE_GLOSSARY
from .recommender import recommend
from .state import (
    STATE_STORE,
    ConversationState,
    EmotionPoint,
    Stage,
    Urgency,
)


# ---------- schema ----------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "update_emotional_state",
        "description": (
            "Quietly log an emotional signal you noticed from the caller. "
            "Call this whenever you hear a clear cue — guilt, anxiety, relief, hesitation, "
            "fatigue, urgency. The caller does not hear this. Never narrate it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "enum": [
                        "guilt",
                        "anxiety",
                        "stress",
                        "uncertainty",
                        "helplessness",
                        "relief",
                        "hesitation",
                        "fatigue",
                        "urgency",
                        "confusion",
                    ],
                },
                "intensity": {"type": "integer", "minimum": 1, "maximum": 5},
            },
            "required": ["label", "intensity"],
        },
    },
    {
        "name": "assess_care_risk",
        "description": (
            "Record what you have learned about the parent's situation and compute a "
            "risk profile. Call this once you have a basic picture — you don't need every detail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lives_alone": {"type": "boolean"},
                "city": {"type": "string"},
                "distance_from_family": {
                    "type": "string",
                    "enum": ["same_city", "different_city", "abroad"],
                },
                "mobility": {"type": "string", "enum": ["full", "partial", "limited"]},
                "chronic_conditions": {"type": "array", "items": {"type": "string"}},
                "recent_incidents": {"type": "array", "items": {"type": "string"}},
                "emergency_preparedness": {"type": "integer", "minimum": 0, "maximum": 5},
                "isolation_risk": {"type": "integer", "minimum": 0, "maximum": 5},
                "care_coordination_gap": {"type": "integer", "minimum": 0, "maximum": 5},
                "notes": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "lookup_emoha_service",
        "description": (
            "Look up the exact, brand-approved description of an Emoha service before you "
            "describe it aloud. Use this so you never invent features."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": list(SERVICE_GLOSSARY.keys()),
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "recommend_plan",
        "description": (
            "Recommend an Emoha plan based on what you have learned. The tool returns the "
            "plan name and the *reason it fits this family* — translate that reason into your "
            "own warm spoken words; never read it verbatim."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "schedule_callback",
        "description": (
            "Schedule a callback from a human Emoha care advisor. Call only after the caller "
            "has agreed to speak with someone."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "caller_name": {"type": "string"},
                "phone": {"type": "string"},
                "preferred_window": {
                    "type": "string",
                    "description": "Free-form, e.g. 'tomorrow morning IST' or 'in the next hour'.",
                },
            },
            "required": ["caller_name", "phone", "preferred_window"],
        },
    },
    {
        "name": "escalate_to_human_immediately",
        "description": (
            "Call right away if you detect an active medical emergency, severe distress, "
            "suicidal language, or repeated confusion suggesting the caller themselves needs help. "
            "Continue speaking calmly with the caller after calling this."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "trigger_phrase": {"type": "string"},
            },
            "required": ["reason"],
        },
    },
    {
        "name": "generate_care_summary",
        "description": (
            "Produce a structured handoff summary for the human advisor. Call near the end of "
            "the conversation, after a callback is scheduled."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_stage",
        "description": (
            "Move the conversation forward to a new stage. Useful for keeping the controlled "
            "flow from the brief without locking the model into a rigid state machine."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": [s.value for s in Stage],
                }
            },
            "required": ["stage"],
        },
    },
    {
        "name": "end_call_gracefully",
        "description": (
            "End the call. Use this when the caller has said goodbye / wants to wrap up, "
            "OR when you've completed the meaningful work of the call "
            "(assess_care_risk → recommend_plan → schedule_callback → generate_care_summary) "
            "and the conversation is naturally finishing. Before calling this, your "
            "spoken response should already be a short, warm closing line — the system "
            "waits until you finish speaking, then ends the call so the caller is "
            "taken to the written summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief, internal-only note on why ending now (e.g. 'caller said goodbye', 'plan + callback scheduled').",
                },
            },
            "required": [],
        },
    },
]


# ---------- handlers ----------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _state(conversation_id: str) -> ConversationState:
    return STATE_STORE.get_or_create(conversation_id)


def update_emotional_state(conversation_id: str, label: str, intensity: int) -> dict:
    s = _state(conversation_id)
    s.emotional_timeline.append(EmotionPoint(at=_now(), label=label, intensity=intensity))
    return {"ok": True}


def assess_care_risk(conversation_id: str, **fields: Any) -> dict:
    s = _state(conversation_id)
    p = s.parent
    if "lives_alone" in fields:
        p.lives_alone = fields["lives_alone"]
    if "city" in fields:
        p.city = fields["city"]
    if "distance_from_family" in fields:
        p.distance_from_family = fields["distance_from_family"]
    if "mobility" in fields:
        p.mobility = fields["mobility"]
    if "chronic_conditions" in fields:
        p.chronic_conditions = list(fields["chronic_conditions"])
    if "recent_incidents" in fields:
        p.recent_incidents = list(fields["recent_incidents"])

    r = s.risk
    if "emergency_preparedness" in fields:
        r.emergency_preparedness = int(fields["emergency_preparedness"])
    if "isolation_risk" in fields:
        r.isolation_risk = int(fields["isolation_risk"])
    if "care_coordination_gap" in fields:
        r.care_coordination_gap = int(fields["care_coordination_gap"])
    if "notes" in fields and fields["notes"]:
        r.notes.append(str(fields["notes"]))

    r.assessed = True
    s.urgency = urgency_from_signals(s)
    s.stage = Stage.RISK_ASSESSMENT

    return {
        "risk": {
            "emergency_preparedness": r.emergency_preparedness,
            "isolation_risk": r.isolation_risk,
            "care_coordination_gap": r.care_coordination_gap,
            "care_confidence_score": r.care_confidence,
        },
        "urgency": s.urgency.value,
    }


def lookup_emoha_service(conversation_id: str, service: str) -> dict:
    desc = SERVICE_GLOSSARY.get(service)
    if not desc:
        return {"error": f"unknown service {service}"}
    return {"service": service, "description": desc}


def recommend_plan(conversation_id: str) -> dict:
    s = _state(conversation_id)
    plan, why = recommend(s)
    s.recommended_plan = plan.code
    s.stage = Stage.RECOMMENDATION
    return {
        "plan_code": plan.code,
        "plan_name": plan.name,
        "positioning": plan.positioning,
        "why_it_fits_this_family": why,
        "emotional_benefit": plan.emotional_benefit,
    }


def schedule_callback(
    conversation_id: str, caller_name: str, phone: str, preferred_window: str
) -> dict:
    s = _state(conversation_id)
    s.caller_name = caller_name
    s.callback_scheduled = {
        "caller_name": caller_name,
        "phone": phone,
        "preferred_window": preferred_window,
        "requested_at": _now().isoformat(),
    }
    s.stage = Stage.HANDOFF
    return {"ok": True, "ticket_id": f"emoha-{conversation_id[:8]}"}


def escalate_to_human_immediately(
    conversation_id: str, reason: str, trigger_phrase: str | None = None
) -> dict:
    s = _state(conversation_id)
    s.escalation = {
        "reason": reason,
        "trigger_phrase": trigger_phrase,
        "at": _now().isoformat(),
    }
    s.urgency = Urgency.EMERGENCY
    s.stage = Stage.ESCALATION
    return {"ok": True, "escalated": True, "guidance": "Stay calm with caller, do not hang up."}


def generate_care_summary(conversation_id: str) -> dict:
    s = _state(conversation_id)
    return build_summary(s)


def set_stage(conversation_id: str, stage: str) -> dict:
    s = _state(conversation_id)
    s.stage = Stage(stage)
    return {"stage": s.stage.value}


def end_call_gracefully(conversation_id: str, reason: str | None = None) -> dict:
    """Flag the conversation to end after the bot's current utterance finishes.

    The bot pipeline watches this flag via the `should_end` event passed to
    each tool dispatcher; it lets the closing TTS play out, then queues an
    EndFrame to leave the Daily room. The browser detects the bot leaving
    and auto-navigates to the summary.
    """
    s = _state(conversation_id)
    s.stage = Stage.HANDOFF
    s.escalation = s.escalation  # no change; just keep shape stable
    return {
        "ok": True,
        "ending": True,
        "reason": reason or "natural wrap-up",
    }


HANDLERS: dict[str, Callable[..., dict]] = {
    "update_emotional_state": update_emotional_state,
    "assess_care_risk": assess_care_risk,
    "lookup_emoha_service": lookup_emoha_service,
    "recommend_plan": recommend_plan,
    "schedule_callback": schedule_callback,
    "escalate_to_human_immediately": escalate_to_human_immediately,
    "generate_care_summary": generate_care_summary,
    "set_stage": set_stage,
    "end_call_gracefully": end_call_gracefully,
}


def dispatch(name: str, conversation_id: str, arguments: dict[str, Any]) -> dict:
    handler = HANDLERS.get(name)
    if handler is None:
        result: dict = {"error": f"unknown tool {name}"}
    else:
        try:
            result = handler(conversation_id=conversation_id, **arguments)
        except TypeError as e:
            result = {"error": f"bad arguments for {name}: {e}"}

    # Persist asynchronously so the LLM/TTS path never blocks on DB. Also
    # re-upsert the conversation snapshot so its mutable fields (risk,
    # callback, urgency, plan) stay in sync after each tool ran.
    try:
        from . import db
        if db.is_enabled():
            db.fire_and_forget(db.insert_tool_call(conversation_id, name, arguments, result))
            state = STATE_STORE.get(conversation_id)
            if state is not None:
                db.fire_and_forget(db.upsert_conversation(state.to_dict(), None))
    except Exception:
        pass

    return result


AsyncHandler = Callable[..., Awaitable[dict]]
