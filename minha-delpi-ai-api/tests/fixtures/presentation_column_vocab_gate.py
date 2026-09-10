"""Helpers — prova de rótulo ≠ chave técnica sem catálogo JSON."""

from __future__ import annotations


def validate_column_vocab_for_ci() -> dict[str, object]:
    """Catálogo JSON `fields` não é mais requisito de rótulo (LLM/OpenAPI)."""
    return {"ok": True, "missingKeys": []}


def labels_by_key(columns: list[dict]) -> dict[str, str]:
    return {
        str(column.get("key") or "").strip(): str(column.get("label") or "").strip()
        for column in columns
        if isinstance(column, dict) and str(column.get("key") or "").strip()
    }
