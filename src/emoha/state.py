"""Per-conversation state — used by tool handlers and the care summary generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Stage(str, Enum):
    GREETING = "greeting"
    DISCOVERY = "discovery"
    EMOTIONAL_REFLECTION = "emotional_reflection"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATION = "recommendation"
    OBJECTION_HANDLING = "objection_handling"
    ESCALATION = "escalation"
    HANDOFF = "handoff"


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass
class EmotionPoint:
    at: datetime
    label: str
    intensity: int  # 1..5


@dataclass
class ParentSituation:
    lives_alone: bool | None = None
    city: str | None = None
    distance_from_family: str | None = None  # "same_city" | "different_city" | "abroad"
    mobility: str | None = None  # "full" | "partial" | "limited"
    chronic_conditions: list[str] = field(default_factory=list)
    recent_incidents: list[str] = field(default_factory=list)


@dataclass
class RiskProfile:
    emergency_preparedness: int = 0  # 0..5 — higher is better
    isolation_risk: int = 0  # 0..5 — higher is worse
    care_coordination_gap: int = 0  # 0..5 — higher is worse
    notes: list[str] = field(default_factory=list)
    assessed: bool = False  # flips true the first time assess_care_risk is called

    @property
    def care_confidence(self) -> int | None:
        """None when no assessment has happened yet — avoids the misleading
        '10/10' default when the agent never called assess_care_risk."""
        if not self.assessed:
            return None
        gap = (self.isolation_risk + self.care_coordination_gap) // 2
        score = max(0, 10 - gap * 2 + self.emergency_preparedness)
        return min(10, score)


@dataclass
class ConversationState:
    conversation_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stage: Stage = Stage.GREETING
    caller_name: str | None = None
    parent: ParentSituation = field(default_factory=ParentSituation)
    risk: RiskProfile = field(default_factory=RiskProfile)
    emotional_timeline: list[EmotionPoint] = field(default_factory=list)
    recommended_plan: str | None = None
    urgency: Urgency = Urgency.LOW
    callback_scheduled: dict[str, Any] | None = None
    escalation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "started_at": self.started_at.isoformat(),
            "stage": self.stage.value,
            "caller_name": self.caller_name,
            "parent": {
                "lives_alone": self.parent.lives_alone,
                "city": self.parent.city,
                "distance_from_family": self.parent.distance_from_family,
                "mobility": self.parent.mobility,
                "chronic_conditions": list(self.parent.chronic_conditions),
                "recent_incidents": list(self.parent.recent_incidents),
            },
            "risk": {
                "emergency_preparedness": self.risk.emergency_preparedness,
                "isolation_risk": self.risk.isolation_risk,
                "care_coordination_gap": self.risk.care_coordination_gap,
                "notes": list(self.risk.notes),
                "care_confidence": self.risk.care_confidence,
            },
            "emotional_timeline": [
                {"at": p.at.isoformat(), "label": p.label, "intensity": p.intensity}
                for p in self.emotional_timeline
            ],
            "recommended_plan": self.recommended_plan,
            "urgency": self.urgency.value,
            "callback_scheduled": self.callback_scheduled,
            "escalation": self.escalation,
        }


class StateStore:
    """In-memory state store. Swap for Redis in production."""

    def __init__(self) -> None:
        self._store: dict[str, ConversationState] = {}

    def get_or_create(self, conversation_id: str) -> ConversationState:
        if conversation_id not in self._store:
            self._store[conversation_id] = ConversationState(conversation_id=conversation_id)
        return self._store[conversation_id]

    def get(self, conversation_id: str) -> ConversationState | None:
        return self._store.get(conversation_id)


STATE_STORE = StateStore()
