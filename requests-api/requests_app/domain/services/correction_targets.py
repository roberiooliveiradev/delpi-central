"""Normalização e catálogo de campos marcáveis na devolução."""

from __future__ import annotations

import re
from typing import Any

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MAX_TARGETS = 32

# Catálogo canônico por type_code (labels PT só para docs/API; UI MFE espelha).
CORRECTION_TARGET_CATALOG: dict[str, tuple[str, ...]] = {
    "invoice-issuance": (
        "recipient",
        "invoice_type",
        "items",
        "freight",
        "extras",
    ),
    "raw-material-creation": (
        "description",
        "unit",
        "notes",
    ),
}


def allowed_correction_targets(type_code: str) -> frozenset[str]:
    return frozenset(CORRECTION_TARGET_CATALOG.get(type_code) or ())


def normalize_correction_targets(
    raw: Any,
    *,
    type_code: str | None = None,
) -> list[str]:
    """Aceita list/tuple; filtra inválidos; se type_code, restringe ao catálogo."""
    if raw is None:
        return []
    if isinstance(raw, str):
        candidates = [raw]
    elif isinstance(raw, (list, tuple)):
        candidates = list(raw)
    else:
        return []

    allowed = allowed_correction_targets(type_code) if type_code else None
    out: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if not isinstance(item, str):
            continue
        key = item.strip().lower()
        if not key or key in seen:
            continue
        if not _KEY_RE.match(key):
            continue
        if allowed is not None and key not in allowed:
            continue
        seen.add(key)
        out.append(key)
        if len(out) >= _MAX_TARGETS:
            break
    return out
