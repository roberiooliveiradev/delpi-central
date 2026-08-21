"""Catálogo declarativo da Análise de problemas (``content/problem_analysis.json``).

Fonte única de títulos, severidades e limites da área. Quem consome lê daqui —
nada de literal espalhado em serviço ou rota.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "problem_analysis.json"


@lru_cache(maxsize=1)
def problem_analysis_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def detector_catalog() -> list[dict[str, Any]]:
    """Entradas do catálogo, já ordenadas pelo campo ``order``."""
    raw = problem_analysis_settings().get("detectors")
    entries = [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
    return sorted(entries, key=lambda item: (as_int(item.get("order"), 0), str(item.get("id"))))


def detector_entry(detector_id: str) -> dict[str, Any] | None:
    target = str(detector_id or "").strip()
    return next((item for item in detector_catalog() if str(item.get("id")) == target), None)


def delayed_order_settings() -> tuple[int, str]:
    """(dias para crítico, template do título) da OP atrasada."""
    cfg = problem_analysis_settings()
    titles = cfg.get("titles") if isinstance(cfg.get("titles"), dict) else {}
    return (
        as_int(cfg.get("criticalDelayDays"), 7),
        str(titles.get("delayedOrder") or "OP {order} atrasada ({days} dias)"),
    )
