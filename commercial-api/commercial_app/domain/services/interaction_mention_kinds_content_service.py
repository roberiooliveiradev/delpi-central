from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "interaction_mention_kinds.json"
)

_REQUIRED_KIND_FIELDS = (
    "id",
    "group",
    "label",
    "hrefStrategy",
    "suggestEnabled",
    "previewEnabled",
)


@lru_cache(maxsize=1)
def load_interaction_mention_kinds() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("interaction_mention_kinds.json deve ser um objeto.")
    kinds = payload.get("kinds")
    if not isinstance(kinds, list) or not kinds:
        raise ValueError("interaction_mention_kinds.json precisa de kinds[] não vazio.")
    for item in kinds:
        if not isinstance(item, dict):
            raise ValueError("Cada kind deve ser um objeto.")
        missing = [field for field in _REQUIRED_KIND_FIELDS if field not in item]
        if missing:
            raise ValueError(f"Kind incompleto; faltam: {', '.join(missing)}.")
        kind_id = str(item.get("id") or "").strip()
        if not kind_id:
            raise ValueError("Kind sem id.")
    return payload


class InteractionMentionKindsContentService:
    """Loader canônico do catálogo de menções da sala (kinds + href)."""

    @classmethod
    def clear_cache(cls) -> None:
        load_interaction_mention_kinds.cache_clear()

    @classmethod
    def bundle(cls) -> dict[str, Any]:
        return load_interaction_mention_kinds()

    @classmethod
    def kinds(cls) -> list[dict[str, Any]]:
        items = cls.bundle().get("kinds") or []
        return [item for item in items if isinstance(item, dict)]

    @classmethod
    def kind_ids(cls) -> frozenset[str]:
        return frozenset(str(item["id"]) for item in cls.kinds())

    @classmethod
    def is_known(cls, kind_id: str) -> bool:
        return str(kind_id or "").strip() in cls.kind_ids()

    @classmethod
    def get(cls, kind_id: str) -> dict[str, Any] | None:
        wanted = str(kind_id or "").strip()
        for item in cls.kinds():
            if str(item.get("id") or "") == wanted:
                return item
        return None

    @classmethod
    def suggest_enabled_ids(cls) -> frozenset[str]:
        return frozenset(
            str(item["id"])
            for item in cls.kinds()
            if item.get("suggestEnabled") is True
        )

    @classmethod
    def group_label(cls, group_id: str) -> str:
        groups = cls.bundle().get("groups") or {}
        if not isinstance(groups, dict):
            return group_id
        return str(groups.get(group_id) or group_id)
