"""Códigos RBAC do módulo Painéis TV — alinhados a tv-dashboard.manifest.json."""

from __future__ import annotations

TV_VIEW_CONSOLIDATED = "tv-dashboard.view.consolidated"

VIEW_FILIAL: dict[str, str] = {
    "01": "tv-dashboard.view.filial-01",
    "02": "tv-dashboard.view.filial-02",
}


def branch_codes_from_permissions(permissions: list[str]) -> list[str]:
    return sorted(codigo for codigo, perm in VIEW_FILIAL.items() if perm in permissions)
