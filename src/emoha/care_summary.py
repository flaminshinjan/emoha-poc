"""Generate the structured handoff summary the human advisor reads before calling back."""

from __future__ import annotations

from .knowledge import PLANS
from .state import ConversationState, Urgency


def build_summary(state: ConversationState) -> dict:
    parent = state.parent
    risk = state.risk

    emotional_arc = _emotional_arc(state)

    plan_name = None
    if state.recommended_plan and state.recommended_plan in PLANS:
        plan_name = PLANS[state.recommended_plan].name

    return {
        "conversation_id": state.conversation_id,
        "caller": {
            "name": state.caller_name,
        },
        "family_situation": {
            "parent_lives_alone": parent.lives_alone,
            "parent_city": parent.city,
            "distance_from_family": parent.distance_from_family,
            "mobility": parent.mobility,
            "chronic_conditions": parent.chronic_conditions,
            "recent_incidents": parent.recent_incidents,
        },
        "emotional_concerns": emotional_arc,
        "risk_indicators": {
            "emergency_preparedness": risk.emergency_preparedness,
            "isolation_risk": risk.isolation_risk,
            "care_coordination_gap": risk.care_coordination_gap,
            "care_confidence_score": risk.care_confidence,
            "notes": risk.notes,
        },
        "recommended_plan": plan_name,
        "urgency": state.urgency.value,
        "callback": state.callback_scheduled,
        "escalation": state.escalation,
    }


def _emotional_arc(state: ConversationState) -> dict:
    if not state.emotional_timeline:
        return {"dominant": None, "trend": "flat", "points": []}

    counts: dict[str, int] = {}
    for p in state.emotional_timeline:
        counts[p.label] = counts.get(p.label, 0) + p.intensity
    dominant = max(counts, key=counts.get)

    first = state.emotional_timeline[0].intensity
    last = state.emotional_timeline[-1].intensity
    trend = "easing" if last < first else "rising" if last > first else "flat"

    return {
        "dominant": dominant,
        "trend": trend,
        "points": [
            {"label": p.label, "intensity": p.intensity, "at": p.at.isoformat()}
            for p in state.emotional_timeline
        ],
    }


def urgency_from_signals(state: ConversationState) -> Urgency:
    if state.escalation:
        return Urgency.EMERGENCY
    if state.risk.emergency_preparedness <= 1 and state.parent.recent_incidents:
        return Urgency.HIGH
    if state.risk.isolation_risk >= 4:
        return Urgency.MEDIUM
    return Urgency.LOW
