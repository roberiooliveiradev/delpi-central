from __future__ import annotations

from functools import lru_cache

from financial_app.application.services.content_loader import load_content
from financial_app.core.security import FIN_ACCESS, can
from financial_app.domain.services.branch_access_service import BranchAccessService
from financial_app.domain.subplugin import Subplugin


@lru_cache(maxsize=1)
def load_subplugin_catalog() -> tuple[Subplugin, ...]:
    raw = load_content("subplugins.json")
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
                permission=str(item.get("permission") or FIN_ACCESS).strip(),
            )
        )
    return tuple(item for item in catalog if item.id)


class SubpluginCatalogService:
    def __init__(self, *, branch_access: BranchAccessService | None = None) -> None:
        self._branch_access = branch_access or BranchAccessService()

    def list_visible(self, user: object | None) -> list[Subplugin]:
        self._branch_access.assert_can_access(user)
        return [item for item in load_subplugin_catalog() if can(user, item.permission)]
