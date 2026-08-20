from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from production_control_app.core.security import PC_ACCESS, can
from production_control_app.domain.subplugin import Subplugin

_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"


@lru_cache(maxsize=1)
def load_subplugin_catalog() -> tuple[Subplugin, ...]:
    raw = json.loads((_CONTENT_DIR / "subplugins.json").read_text(encoding="utf-8"))
    items = raw.get("items") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return ()
    catalog: list[Subplugin] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status not in {"active", "coming_soon"}:
            continue
        catalog.append(
            Subplugin(
                id=str(item.get("id") or "").strip(),
                label=str(item.get("label") or "").strip(),
                description=str(item.get("description") or "").strip(),
                icon=str(item.get("icon") or "").strip(),
                route=str(item.get("route") or "").strip(),
                status=status,
                permission=str(item.get("permission") or PC_ACCESS).strip(),
            )
        )
    return tuple(item for item in catalog if item.id)


class SubpluginCatalogService:
    def list_visible(self, user: object | None) -> list[Subplugin]:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")
        visible: list[Subplugin] = []
        for item in load_subplugin_catalog():
            if can(user, item.permission):
                visible.append(item)
        return visible
