"""Normalização de labels de problema identificado (NC LMP)."""

from __future__ import annotations


def normalize_problem_tag_label(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    if not text:
        return None
    return text[:80]


def normalize_problem_tag_labels(values: list[str] | None) -> list[str]:
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
