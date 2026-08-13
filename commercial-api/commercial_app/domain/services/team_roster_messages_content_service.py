from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "team_roster_messages.json"
)


@lru_cache(maxsize=1)
def load_team_roster_messages() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("team_roster_messages.json deve ser um objeto.")
    return payload


class TeamRosterMessagesContentService:
    """Loader canônico de textos PT-BR do team-roster."""

    @classmethod
    def clear_cache(cls) -> None:
        load_team_roster_messages.cache_clear()

    @classmethod
    def bundle(cls) -> dict[str, Any]:
        return load_team_roster_messages()

    @classmethod
    def error(cls, key: str, **values: str) -> str:
        errors = cls.bundle().get("errors") or {}
        template = str(errors.get(key) or key)
        if not values:
            return template
        try:
            return template.format(**values)
        except Exception:
            return template

    @classmethod
    def message(cls, key: str) -> str:
        messages = cls.bundle().get("messages") or {}
        return str(messages.get(key) or key)
