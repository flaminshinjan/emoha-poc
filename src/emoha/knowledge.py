"""Emoha plans, services, and the brand positioning the agent must reference.

Kept as a single source of truth so the LLM never invents plan names or features.
The agent reaches this through the `lookup_emoha_service` tool — do not paste
this whole blob into the system prompt.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    positioning: str
    suited_for: list[str]
    includes: list[str]
    emotional_benefit: str


PLANS: dict[str, Plan] = {
    "wellness_lite": Plan(
        code="wellness_lite",
        name="Emoha Wellness",
        positioning="A gentle starting point — regular wellness check-ins for parents who are largely independent.",
        suited_for=[
            "parent living alone but mobile",
            "no recent medical incidents",
            "family wants peace of mind without intrusion",
        ],
        includes=[
            "scheduled wellness calls",
            "festival and birthday calls",
            "community engagement invites",
            "family escalation if a check-in is missed",
        ],
        emotional_benefit="Reassurance that someone is checking in, without making parents feel monitored.",
    ),
    "care_plus": Plan(
        code="care_plus",
        name="Emoha Care Plus",
        positioning="Active care coordination for parents who need help with appointments, travel and day-to-day support.",
        suited_for=[
            "parent has chronic conditions",
            "recent hospital visit or fall",
            "family lives in a different city",
        ],
        includes=[
            "Emoha Daughter — a dedicated care coordinator",
            "doctor appointment accompaniment",
            "hospital coordination",
            "medication and refill reminders",
            "wellness calls",
            "emergency response coordination",
        ],
        emotional_benefit="Families can stop being the on-call coordinator and go back to being a son or daughter.",
    ),
    "total_care": Plan(
        code="total_care",
        name="Emoha Total Care",
        positioning="Full-spectrum care for parents who recently had a major event or live with significant health needs.",
        suited_for=[
            "recovery after hospitalisation",
            "limited mobility",
            "NRI families managing remotely",
            "single surviving parent",
        ],
        includes=[
            "everything in Care Plus",
            "priority emergency response",
            "home visits by care managers",
            "travel coordination across cities",
            "extended family communication updates",
            "emotional wellbeing sessions",
        ],
        emotional_benefit="Parents stay at home, independent and supported — the family is never alone in this.",
    ),
}


SERVICE_GLOSSARY: dict[str, str] = {
    "emoha_daughter": (
        "A dedicated care coordinator who acts like an extended family member — "
        "calls parents, coordinates appointments and keeps the family in the loop."
    ),
    "emergency_response": (
        "24x7 coordination during medical emergencies — Emoha steps in to call an ambulance, "
        "coordinate with the hospital and inform the family, often before the family knows."
    ),
    "appointment_accompaniment": (
        "A trained Emoha team member physically accompanies the parent to a doctor visit, "
        "captures what the doctor said and shares notes with the family."
    ),
    "travel_coordination": (
        "When parents need to travel between cities for care or to visit family, "
        "Emoha arranges the logistics — booking, escort, hospital transfer."
    ),
    "wellness_calls": (
        "Regular friendly calls to check on parents' wellbeing — not medical, just human warmth."
    ),
    "community_engagement": (
        "Activities, events and group calls that reduce loneliness and give parents a sense of belonging."
    ),
}


BRAND_PILLARS: list[str] = [
    "Help parents stay independent — safely.",
    "Be the extended family that lives near the parent.",
    "Take coordination work off the adult child's shoulders.",
    "Reassure, never alarm.",
]
