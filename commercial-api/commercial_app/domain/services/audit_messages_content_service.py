from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "pt-BR" / "audit_messages.json"
)


@lru_cache(maxsize=1)
def load_audit_messages() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("audit_messages.json deve ser um objeto.")
    return payload


class AuditMessagesContentService:
    """Loader canônico de textos PT-BR de auditoria (JSON)."""

    @classmethod
    def clear_cache(cls) -> None:
        load_audit_messages.cache_clear()

    @classmethod
    def bundle(cls) -> dict[str, Any]:
        return load_audit_messages()

    @classmethod
    def title_for(cls, action: str) -> str:
        titles = cls.bundle().get("titles") or {}
        fallback = (cls.bundle().get("fallback") or {}).get("title") or "Evento de auditoria"
        return str(titles.get(action) or fallback)

    @classmethod
    def message_template_for(cls, action: str) -> str:
        messages = cls.bundle().get("messages") or {}
        fallback = (cls.bundle().get("fallback") or {}).get("message") or "Ação «{action}» registrada."
        return str(messages.get(action) or fallback)

    @classmethod
    def tone_for(cls, action: str) -> str:
        tones = cls.bundle().get("tones") or {}
        fallback = (cls.bundle().get("fallback") or {}).get("tone") or "default"
        return str(tones.get(action) or fallback)

    @classmethod
    def role_label(cls, role: str) -> str:
        labels = cls.bundle().get("roleLabels") or {}
        normalized = (role or "").strip().lower()
        return str(labels.get(normalized) or role or "membro")
