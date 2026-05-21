"""Rule-based plan recommender. Deterministic so the demo is auditable."""

from __future__ import annotations

from .knowledge import PLANS, Plan
from .state import ConversationState


def recommend(state: ConversationState) -> tuple[Plan, str]:
    """Return (plan, why_it_fits) — a short narrative the LLM can paraphrase aloud."""
    parent = state.parent
    risk = state.risk

    incidents = [i.lower() for i in parent.recent_incidents]
    serious_incident = any(k in " ".join(incidents) for k in ("fall", "hospital", "stroke", "surgery"))

    chronic = bool(parent.chronic_conditions)
    nri = parent.distance_from_family == "abroad"
    different_city = parent.distance_from_family in {"different_city", "abroad"}
    limited_mobility = parent.mobility == "limited"
    high_isolation = risk.isolation_risk >= 3
    low_prep = risk.emergency_preparedness <= 2

    if serious_incident and (limited_mobility or nri or low_prep):
        plan = PLANS["total_care"]
        why = (
            "Given the recent event and how far you are from each other, the priority is "
            "having someone close by who can step in for emergencies, home visits and travel — "
            "so you are never the only person on call."
        )
    elif chronic or different_city or (serious_incident and not limited_mobility) or low_prep:
        plan = PLANS["care_plus"]
        why = (
            "What seems most useful for your family is having a dedicated coordinator — an Emoha Daughter — "
            "who handles appointments, medication reminders and emergency coordination, so you can stop "
            "being the on-call manager from far away."
        )
    else:
        plan = PLANS["wellness_lite"]
        why = (
            "Things sound largely under control today. A lighter starting point — regular wellness "
            "check-ins and someone watching quietly in the background — often gives families peace of "
            "mind without making parents feel monitored."
        )

    if high_isolation and plan.code == "wellness_lite":
        # Bias up if loneliness is the dominant signal.
        plan = PLANS["care_plus"]
        why += (
            " Loneliness is a real risk on its own, and Care Plus also opens up community engagement "
            "and a friendly coordinator who calls regularly."
        )

    return plan, why
