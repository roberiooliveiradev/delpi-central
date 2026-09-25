"""Canonical text typography transforms for PresentationMutation (RIBBON-TEXT-001)."""

from __future__ import annotations

import re
from typing import Any

_CASE_MODES = frozenset({"sentence", "lower", "upper", "title", "toggle"})
_FONT_SIZE_MIN = 12
_FONT_SIZE_STEP = 2
_INDENT_MAX = 8


def clamp_font_size(size: float) -> int:
    value = int(round(size))
    return max(_FONT_SIZE_MIN, value)


def bump_font_size(current: Any, delta_steps: int, *, fallback: float = 28) -> int:
    try:
        base = float(current)
    except (TypeError, ValueError):
        base = float(fallback)
    if not (base == base):  # NaN
        base = float(fallback)
    return clamp_font_size(base + int(delta_steps) * _FONT_SIZE_STEP)


def clamp_indent_level(raw: Any) -> int:
    try:
        level = int(raw)
    except (TypeError, ValueError):
        return 0
    return max(0, min(_INDENT_MAX, level))


def transform_text_case(text: str, mode: str) -> str:
    """Mutate content casing (pt-BR). Not CSS text-transform."""
    if not text:
        return text
    token = str(mode or "").strip().lower()
    if token not in _CASE_MODES:
        return text
    if token == "lower":
        return text.lower()
    if token == "upper":
        return text.upper()
    if token == "title":
        # Capitalize letter after start or non-letter/digit (Unicode-aware).
        out: list[str] = []
        prev_boundary = True
        for ch in text.lower():
            if prev_boundary and ch.isalpha():
                out.append(ch.upper())
                prev_boundary = False
            else:
                out.append(ch)
                prev_boundary = not (ch.isalnum())
        return "".join(out)
    if token == "toggle":
        return "".join(
            ch.lower() if ch.isupper() else ch.upper() if ch.islower() else ch for ch in text
        )
    # sentence: first letter of string
    lowered = text.lower()
    for i, ch in enumerate(lowered):
        if ch.isalpha():
            return lowered[:i] + ch.upper() + lowered[i + 1 :]
    return lowered


def transform_content_runs_case(
    runs: list[Any], mode: str, *, start: int | None = None, end: int | None = None
) -> list[dict[str, Any]]:
    """Transform case on authoring runs. dataRef runs stay atomic.

    Optional start/end are plain-text offsets over concatenated run texts
    (dataRef placeholder length = len(text) or 1 for empty).
    """
    if start is None or end is None or start >= end:
        out: list[dict[str, Any]] = []
        for raw in runs:
            if not isinstance(raw, dict):
                continue
            run = dict(raw)
            data_ref = run.get("dataRef")
            if isinstance(data_ref, dict) and str(data_ref.get("field") or "").strip():
                out.append(run)
                continue
            text = run.get("text")
            if isinstance(text, str):
                run["text"] = transform_text_case(text, mode)
            out.append(run)
        return out

    safe_start = max(0, int(start))
    safe_end = max(safe_start, int(end))
    out = []
    pos = 0
    for raw in runs:
        if not isinstance(raw, dict):
            continue
        run = dict(raw)
        data_ref = run.get("dataRef")
        text = run.get("text") if isinstance(run.get("text"), str) else ""
        if isinstance(data_ref, dict) and str(data_ref.get("field") or "").strip():
            length = len(text) if text else 1
            pos += length
            out.append(run)
            continue
        length = len(text)
        run_start = pos
        run_end = pos + length
        pos = run_end
        if run_end <= safe_start or run_start >= safe_end:
            out.append(run)
            continue
        local_start = max(0, safe_start - run_start)
        local_end = min(length, safe_end - run_start)
        before = text[:local_start]
        mid = transform_text_case(text[local_start:local_end], mode)
        after = text[local_end:]
        run["text"] = f"{before}{mid}{after}"
        out.append(run)
    return out


def normalize_run_style(style: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(style, dict):
        return None
    out = dict(style)
    shift = out.get("baselineShift")
    if shift not in {"sub", "super"}:
        out.pop("baselineShift", None)
    else:
        # Mutual exclusion already a single value.
        out["baselineShift"] = shift
    if "indentLevel" in out:
        level = clamp_indent_level(out.get("indentLevel"))
        if level > 0:
            out["indentLevel"] = level
        else:
            out.pop("indentLevel", None)
    return out


def normalize_block_text_style(style: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(style, dict):
        return None
    out = dict(style)
    shift = out.get("baselineShift")
    if shift not in {"sub", "super"}:
        out.pop("baselineShift", None)
    if "indentLevel" in out:
        level = clamp_indent_level(out.get("indentLevel"))
        if level > 0:
            out["indentLevel"] = level
        else:
            out.pop("indentLevel", None)
    for key in ("paragraphSpacingBefore", "paragraphSpacingAfter"):
        raw = out.get(key)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            out.pop(key, None)
            continue
        if value <= 0 or value != value:
            out.pop(key, None)
        else:
            out[key] = value
    return out


def plain_from_runs(runs: list[Any]) -> str:
    parts: list[str] = []
    for run in runs:
        if isinstance(run, dict) and isinstance(run.get("text"), str):
            parts.append(run["text"])
    return "".join(parts)
