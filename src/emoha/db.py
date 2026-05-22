"""Postgres persistence layer (asyncpg pool + tiny query helpers).

Schema is created idempotently on first connection — no migration framework
because the schema is small and the demo is single-tenant. If this graduates
to production, swap to Alembic.

All writes from the hot path (tool calls, transcript lines) are wrapped in
`fire_and_forget(...)` so a DB hiccup never blocks the LLM/TTS pipeline.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional

from loguru import logger

try:
    import asyncpg  # type: ignore
except ImportError:  # asyncpg only present in prod Docker image
    asyncpg = None  # type: ignore


_pool: Optional["asyncpg.Pool"] = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id                      UUID PRIMARY KEY,
    started_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    caller_name             TEXT,
    parent_name             TEXT,
    parent_relation         TEXT,
    city                    TEXT,
    lives_alone             BOOLEAN,
    distance_from_family    TEXT,
    mobility                TEXT,
    chronic_conditions      JSONB NOT NULL DEFAULT '[]'::jsonb,
    recent_incidents        JSONB NOT NULL DEFAULT '[]'::jsonb,
    opening_note            TEXT,
    stage                   TEXT,
    urgency                 TEXT,
    risk_assessed           BOOLEAN NOT NULL DEFAULT FALSE,
    emergency_preparedness  INT NOT NULL DEFAULT 0,
    isolation_risk          INT NOT NULL DEFAULT 0,
    care_coordination_gap   INT NOT NULL DEFAULT 0,
    risk_notes              JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommended_plan        TEXT,
    callback                JSONB,
    escalation              JSONB,
    advisor_slug            TEXT,
    raw_state               JSONB
);

CREATE INDEX IF NOT EXISTS conversations_started_at_idx ON conversations (started_at DESC);

CREATE TABLE IF NOT EXISTS transcript_lines (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    role            TEXT NOT NULL,
    text            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS transcript_lines_conv_at_idx
    ON transcript_lines (conversation_id, at);

CREATE TABLE IF NOT EXISTS tool_calls (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name            TEXT NOT NULL,
    arguments       JSONB,
    result          JSONB
);

CREATE INDEX IF NOT EXISTS tool_calls_conv_at_idx
    ON tool_calls (conversation_id, at);
"""


def is_enabled() -> bool:
    """True only when both asyncpg is importable and DATABASE_URL is set.

    Lets the bot run locally without Postgres — DB writes silently no-op.
    """
    return asyncpg is not None and bool(os.environ.get("DATABASE_URL"))


async def get_pool() -> Optional["asyncpg.Pool"]:
    global _pool
    if not is_enabled():
        return None
    if _pool is None:
        url = os.environ["DATABASE_URL"]
        # asyncpg wants `postgres://` rather than `postgresql://` for SSL
        # negotiation on managed providers; both accepted by Fly MPG.
        try:
            _pool = await asyncpg.create_pool(
                url, min_size=1, max_size=8, command_timeout=10,
                statement_cache_size=0,  # pgbouncer compatibility
            )
            async with _pool.acquire() as conn:
                await conn.execute(SCHEMA_SQL)
            logger.info("emoha db pool ready + schema ensured")
        except Exception:
            logger.exception("emoha db pool init failed — running without persistence")
            _pool = None
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def fire_and_forget(coro) -> None:
    """Schedule a write without blocking the caller, log any failure."""
    async def _wrap():
        try:
            await coro
        except Exception:
            logger.exception("emoha db write failed (non-fatal)")
    try:
        asyncio.get_event_loop().create_task(_wrap())
    except RuntimeError:
        # No running loop (synchronous context) — skip.
        pass


# ---------- writes ----------

async def upsert_conversation(state: dict[str, Any], advisor_slug: Optional[str]) -> None:
    pool = await get_pool()
    if pool is None:
        return
    parent = state.get("parent", {})
    risk = state.get("risk", {})
    callback = state.get("callback_scheduled")
    escalation = state.get("escalation")
    notes = risk.get("notes") or []
    opening = notes[-1] if notes else None
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conversations (
                id, started_at, updated_at,
                caller_name, parent_name, parent_relation, city, lives_alone,
                distance_from_family, mobility, chronic_conditions, recent_incidents,
                opening_note, stage, urgency, risk_assessed,
                emergency_preparedness, isolation_risk, care_coordination_gap, risk_notes,
                recommended_plan, callback, escalation, advisor_slug, raw_state
            ) VALUES (
                $1, $2, NOW(),
                $3, $4, $5, $6, $7,
                $8, $9, $10::jsonb, $11::jsonb,
                $12, $13, $14, $15,
                $16, $17, $18, $19::jsonb,
                $20, $21::jsonb, $22::jsonb, $23, $24::jsonb
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = NOW(),
                caller_name = EXCLUDED.caller_name,
                parent_name = EXCLUDED.parent_name,
                parent_relation = EXCLUDED.parent_relation,
                city = EXCLUDED.city,
                lives_alone = EXCLUDED.lives_alone,
                distance_from_family = EXCLUDED.distance_from_family,
                mobility = EXCLUDED.mobility,
                chronic_conditions = EXCLUDED.chronic_conditions,
                recent_incidents = EXCLUDED.recent_incidents,
                opening_note = EXCLUDED.opening_note,
                stage = EXCLUDED.stage,
                urgency = EXCLUDED.urgency,
                risk_assessed = EXCLUDED.risk_assessed,
                emergency_preparedness = EXCLUDED.emergency_preparedness,
                isolation_risk = EXCLUDED.isolation_risk,
                care_coordination_gap = EXCLUDED.care_coordination_gap,
                risk_notes = EXCLUDED.risk_notes,
                recommended_plan = EXCLUDED.recommended_plan,
                callback = EXCLUDED.callback,
                escalation = EXCLUDED.escalation,
                advisor_slug = COALESCE(conversations.advisor_slug, EXCLUDED.advisor_slug),
                raw_state = EXCLUDED.raw_state
            """,
            state["conversation_id"],
            _ts(state.get("started_at")) or datetime.now(),
            state.get("caller_name"),
            state.get("parent_name"),  # currently not in state model, future-proof
            state.get("parent_relation"),
            parent.get("city"),
            parent.get("lives_alone"),
            parent.get("distance_from_family"),
            parent.get("mobility"),
            json.dumps(parent.get("chronic_conditions") or []),
            json.dumps(parent.get("recent_incidents") or []),
            opening,
            state.get("stage"),
            state.get("urgency"),
            bool(risk.get("emergency_preparedness") or risk.get("isolation_risk") or risk.get("care_coordination_gap")),
            int(risk.get("emergency_preparedness") or 0),
            int(risk.get("isolation_risk") or 0),
            int(risk.get("care_coordination_gap") or 0),
            json.dumps(notes),
            state.get("recommended_plan"),
            json.dumps(callback) if callback else None,
            json.dumps(escalation) if escalation else None,
            advisor_slug,
            json.dumps(state),
        )


async def insert_transcript(conversation_id: str, role: str, text: str) -> None:
    pool = await get_pool()
    if pool is None:
        return
    async with pool.acquire() as conn:
        # Ensure parent row exists so the FK doesn't reject early lines.
        await conn.execute(
            "INSERT INTO conversations (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
            conversation_id,
        )
        await conn.execute(
            "INSERT INTO transcript_lines (conversation_id, role, text) VALUES ($1, $2, $3)",
            conversation_id, role, text,
        )


async def insert_tool_call(
    conversation_id: str, name: str, arguments: dict[str, Any], result: Any
) -> None:
    pool = await get_pool()
    if pool is None:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO conversations (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
            conversation_id,
        )
        await conn.execute(
            "INSERT INTO tool_calls (conversation_id, name, arguments, result) "
            "VALUES ($1, $2, $3::jsonb, $4::jsonb)",
            conversation_id, name,
            json.dumps(arguments or {}),
            json.dumps(_json_safe(result)),
        )


# ---------- reads ----------

async def list_conversations(limit: int = 50) -> list[dict[str, Any]]:
    pool = await get_pool()
    if pool is None:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id::text, started_at, updated_at, caller_name, parent_name,
                   city, urgency, recommended_plan, stage,
                   (SELECT COUNT(*) FROM transcript_lines tl WHERE tl.conversation_id = c.id) AS turn_count,
                   (SELECT COUNT(*) FROM tool_calls tc WHERE tc.conversation_id = c.id) AS tool_count
            FROM conversations c
            ORDER BY started_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]


async def fetch_conversation(conversation_id: str) -> Optional[dict[str, Any]]:
    pool = await get_pool()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM conversations WHERE id = $1", conversation_id,
        )
        if row is None:
            return None
        transcript = await conn.fetch(
            "SELECT at, role, text FROM transcript_lines "
            "WHERE conversation_id = $1 ORDER BY at, id",
            conversation_id,
        )
        tools = await conn.fetch(
            "SELECT at, name, arguments, result FROM tool_calls "
            "WHERE conversation_id = $1 ORDER BY at, id",
            conversation_id,
        )
    return {
        "conversation": {
            k: _coerce(v) for k, v in dict(row).items()
        },
        "transcript": [
            {"at": r["at"].isoformat(), "role": r["role"], "text": r["text"]}
            for r in transcript
        ],
        "tool_calls": [
            {
                "at": r["at"].isoformat(),
                "name": r["name"],
                "arguments": _decode_json(r["arguments"]),
                "result": _decode_json(r["result"]),
            }
            for r in tools
        ],
    }


# ---------- helpers ----------

def _ts(v) -> Optional[datetime]:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _coerce(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, (str, int, float, bool, list, dict, type(None))):
        return v
    return _decode_json(v)


def _decode_json(v):
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


def _json_safe(v):
    """Make dicts JSON-serialisable (strip datetimes etc.)."""
    try:
        json.dumps(v)
        return v
    except TypeError:
        if isinstance(v, dict):
            return {k: _json_safe(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_json_safe(x) for x in v]
        return str(v)
