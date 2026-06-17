"""Campos técnicos de payloads operacionais — não exibir em KPI, narrativa ou cobertura duplicada."""

from __future__ import annotations

from typing import Any

_TECHNICAL_SUMMARY_KEYS = frozenset(
    {
        "is_complete",
        "branch_filter_applied",
        "consolidated_across_branches",
    }
)


class ChatPresentationOperationalMetadataFieldService:
    @classmethod
    def is_technical_summary_key(cls, key: str) -> bool:
        return str(key or "").strip() in _TECHNICAL_SUMMARY_KEYS

    @classmethod
    def filter_summary(cls, summary: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(summary, dict):
            return {}

        return {
            key: value
            for key, value in summary.items()
            if not cls.is_technical_summary_key(str(key))
        }
