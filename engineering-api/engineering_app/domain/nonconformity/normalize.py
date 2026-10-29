"""Normalização de inputs do contexto NC (tags, textos, produtos)."""

from __future__ import annotations

from typing import Any


def normalize_problem_tag_label(value: str | None) -> str | None:
    """Normaliza label de problema identificado: colapsa espaços, ≤80 chars."""
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    if not text:
        return None
    return text[:80]


def normalize_problem_tag_labels(values: list[str] | None) -> list[str]:
    """Dedup case-insensitive preservando primeira grafia, ordem estável."""
    if not values:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        label = normalize_problem_tag_label(raw)
        if not label:
            continue
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def normalize_text(value: Any, *, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if max_len is not None:
        return text[:max_len]
    return text


def normalize_products(values: Any) -> list[dict[str, str]]:
    """Dedup por código (upper), ordena por código — semântica do legado."""
    if not isinstance(values, list):
        return []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, dict):
            continue
        code = normalize_text(raw.get("product_code") or raw.get("code"))
        if not code:
            continue
        key = code.upper()
        if key in seen:
            continue
        seen.add(key)
        description = normalize_text(
            raw.get("product_description") or raw.get("description")
        )
        out.append(
            {
                "product_code": key,
                "product_description": description or "",
            }
        )
    out.sort(key=lambda item: item["product_code"])
    return out
