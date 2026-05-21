"""Runtime configuration loaded from environment."""

import re
from functools import lru_cache
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_LEADING_COMMENT_RE = re.compile(r"^\s*#")
_TRAILING_COMMENT_RE = re.compile(r"\s+#.*$")


def _strip_inline_comment(value: Any) -> Any:
    """Strip stray inline `# comment` tails from env values and treat placeholders as empty.

    pydantic-settings reads everything after `=` literally; if a `.env` line is
    `KEY=    # optional — comment`, dotenv may hand us `"# optional — comment"`
    (whitespace already trimmed but the comment still attached). We need to
    drop the whole thing — there is no real value here.
    """
    if not isinstance(value, str):
        return value
    s = value.strip()
    # Whole value is just a comment — treat as missing
    if _LEADING_COMMENT_RE.match(s):
        return None
    # `actual_value   # trailing comment` — keep actual_value
    s = _TRAILING_COMMENT_RE.sub("", s).strip()
    if s in ("", "...", "sk-ant-..."):
        return None
    return s


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def _clean(cls, v: Any) -> Any:
        return _strip_inline_comment(v)

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-sonnet-4-6", alias="ANTHROPIC_MODEL")

    deepgram_api_key: Optional[str] = Field(None, alias="DEEPGRAM_API_KEY")
    cartesia_api_key: Optional[str] = Field(None, alias="CARTESIA_API_KEY")
    cartesia_voice_id: str = Field(
        "79a125e8-cd45-4c13-8a67-188112f4dd22", alias="CARTESIA_VOICE_ID"
    )
    cartesia_cloned_voice_id: Optional[str] = Field(None, alias="CARTESIA_CLONED_VOICE_ID")

    tavus_api_key: Optional[str] = Field(None, alias="TAVUS_API_KEY")
    tavus_replica_id: Optional[str] = Field(None, alias="TAVUS_REPLICA_ID")
    tavus_persona_id: Optional[str] = Field(None, alias="TAVUS_PERSONA_ID")

    daily_api_key: Optional[str] = Field(None, alias="DAILY_API_KEY")
    daily_room_url: Optional[str] = Field(None, alias="DAILY_ROOM_URL")

    bland_api_key: Optional[str] = Field(None, alias="BLAND_API_KEY")
    bland_phone_number: Optional[str] = Field(None, alias="BLAND_PHONE_NUMBER")
    bland_webhook_base: Optional[str] = Field(None, alias="BLAND_WEBHOOK_BASE")

    server_host: str = Field("0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(8000, alias="SERVER_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
