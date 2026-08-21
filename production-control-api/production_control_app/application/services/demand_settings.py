"""Catálogo declarativo da Demanda (``content/demand.json``).

Limites, TTL de cache e domínios de ordenação/status ficam no JSON — o serviço
só aplica a regra.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "demand.json"


@lru_cache(maxsize=1)
def demand_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def setting_int(key: str, default: int) -> int:
    try:
        return int(demand_settings().get(key, default))
    except (TypeError, ValueError):
        return default


def setting_list(key: str) -> tuple[str, ...]:
    raw = demand_settings().get(key)
    if not isinstance(raw, list):
        return ()
    return tuple(str(item).strip() for item in raw if str(item).strip())


def setting_str(key: str, default: str) -> str:
    value = str(demand_settings().get(key) or "").strip()
    return value or default
