"""Sanity tests for tool handlers — no network, no LLM. Run: `pytest`."""

from emoha.knowledge import PLANS
from emoha.state import STATE_STORE
from emoha.tools import (
    assess_care_risk,
    escalate_to_human_immediately,
    generate_care_summary,
    lookup_emoha_service,
    recommend_plan,
    schedule_callback,
    update_emotional_state,
)


def test_full_flow_nri_fall_scenario():
    cid = "test-nri-fall"
    # Fresh state per test
    STATE_STORE._store.pop(cid, None)  # type: ignore[attr-defined]

    update_emotional_state(cid, "anxiety", 4)
    update_emotional_state(cid, "guilt", 3)

    risk = assess_care_risk(
        cid,
        lives_alone=True,
        city="Jaipur",
        distance_from_family="abroad",
        mobility="partial",
        recent_incidents=["fall last week"],
        emergency_preparedness=1,
        isolation_risk=4,
        care_coordination_gap=4,
        notes="Daughter in Bangalore, no one local to coordinate",
    )
    assert risk["urgency"] in {"high", "emergency"}
    assert risk["risk"]["care_confidence_score"] <= 6

    rec = recommend_plan(cid)
    assert rec["plan_code"] in {"care_plus", "total_care"}
    assert "Emoha" in rec["plan_name"]

    cb = schedule_callback(
        cid,
        caller_name="Aanya",
        phone="+919999999999",
        preferred_window="tomorrow morning IST",
    )
    assert cb["ok"]

    summary = generate_care_summary(cid)
    assert summary["recommended_plan"] == PLANS[rec["plan_code"]].name
    assert summary["risk_indicators"]["care_confidence_score"] <= 6
    assert summary["emotional_concerns"]["dominant"] in {"anxiety", "guilt"}
    assert summary["callback"]["caller_name"] == "Aanya"


def test_low_risk_path_recommends_wellness():
    cid = "test-low-risk"
    STATE_STORE._store.pop(cid, None)  # type: ignore[attr-defined]

    assess_care_risk(
        cid,
        lives_alone=False,
        city="Pune",
        distance_from_family="same_city",
        mobility="full",
        emergency_preparedness=4,
        isolation_risk=1,
        care_coordination_gap=1,
    )
    rec = recommend_plan(cid)
    assert rec["plan_code"] == "wellness_lite"


def test_lookup_service_returns_brand_copy():
    out = lookup_emoha_service("test-lookup", "emoha_daughter")
    assert "coordinator" in out["description"].lower()


def test_escalation_sets_emergency_urgency():
    cid = "test-escalate"
    STATE_STORE._store.pop(cid, None)  # type: ignore[attr-defined]
    out = escalate_to_human_immediately(cid, reason="severe chest pain mentioned")
    assert out["escalated"]
    summary = generate_care_summary(cid)
    assert summary["urgency"] == "emergency"
    assert summary["escalation"]["reason"] == "severe chest pain mentioned"
