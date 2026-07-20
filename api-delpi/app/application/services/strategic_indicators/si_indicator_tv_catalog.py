"""Loader do catálogo SI para rotas dashboard meta/realizado."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT = Path(__file__).resolve().parents[3] / "content" / "si_indicator_tv_catalog.json"


@lru_cache(maxsize=1)
def load_si_indicator_tv_catalog() -> list[dict[str, str]]:
    payload = json.loads(_CONTENT.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = []
    for item in payload.get("indicators") or []:
        if not isinstance(item, dict):
            continue
        indicator_id = str(item.get("indicatorId") or "").strip()
        if not indicator_id:
            continue
        rows.append(
            {
                "indicator_id": indicator_id,
                "source_key": str(item.get("sourceKey") or "").strip(),
                "name": str(item.get("name") or "").strip(),
                "department_id": str(item.get("departmentId") or "").strip(),
            }
        )
    return rows


def indicator_snake(indicator_id: str) -> str:
    return str(indicator_id or "").strip().replace("-", "_")


def operation_id_for(indicator_id: str, kind: str) -> str:
    return f"get_si_indicator_{indicator_snake(indicator_id)}_{kind}"


def path_for(indicator_id: str, kind: str) -> str:
    return f"/indicators/{indicator_id}/{kind}"


def catalog_by_indicator_id() -> dict[str, dict[str, str]]:
    return {row["indicator_id"]: row for row in load_si_indicator_tv_catalog()}


def reset_si_indicator_tv_catalog_cache() -> None:
    load_si_indicator_tv_catalog.cache_clear()


def department_category(department_id: str) -> str:
    token = str(department_id or "").strip().lower()
    return token or "system"


def locale_labels(name: str, kind: str) -> dict[str, Any]:
    suffix_pt = "realizado" if kind == "realized" else "meta"
    suffix_en = "actual" if kind == "realized" else "goal"
    label_pt = f"{name} — {suffix_pt}"
    label_en = f"{name} — {suffix_en}"
    if kind == "realized":
        desc_pt = f"Valor realizado do indicador SI «{name}» (visão IGD)."
        desc_en = f"Actual value for SI indicator «{name}» (IGD view)."
        when_pt = f"Usar no card KPI do realizado de {name}."
        when_en = f"Use as a KPI card for the actual {name}."
    else:
        desc_pt = f"Meta (comparable goal) do indicador SI «{name}» (visão IGD)."
        desc_en = f"Goal (comparable) for SI indicator «{name}» (IGD view)."
        when_pt = f"Usar no card KPI da meta de {name}."
        when_en = f"Use as a KPI card for the {name} goal."
    return {
        "en": {
            "summary": label_en,
            "description": desc_en,
            "whenToUse": when_en,
            "label": label_en,
        },
        "pt-BR": {
            "summary": label_pt,
            "description": desc_pt,
            "whenToUse": when_pt,
            "label": label_pt,
        },
    }
