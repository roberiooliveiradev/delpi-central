"""Filiais e identidade de centro de custo no Planejamento Orçamentário."""

from __future__ import annotations

from typing import Any

from app.domain.totvs.protheus_branches import (
    PROTHEUS_BRANCH_CODES,
    normalize_branch_code,
)

# Filiais oficiais do planejamento (espelho Protheus).
BUDGET_BRANCH_CODES: tuple[str, ...] = PROTHEUS_BRANCH_CODES

BUDGET_BRANCH_LABELS_PT: dict[str, str] = {
    "01": "Jaraguá do Sul/SC",
    "02": "Rio Bananal/ES",
}

BUDGET_BRANCH_UNIT_NAMES: dict[str, str] = {
    "01": "DELPI Jaraguá — Chicotes",
    "02": "DELPI Espírito Santo",
}

COST_CENTER_SOURCE_MANUAL = "manual"
COST_CENTER_SOURCE_ERP = "erp"
ALLOWED_COST_CENTER_SOURCES = frozenset(
    {COST_CENTER_SOURCE_MANUAL, COST_CENTER_SOURCE_ERP}
)


def normalize_budget_branch(raw: str | None) -> str:
    """Exige filial 01 ou 02."""
    try:
        return normalize_branch_code(raw)
    except ValueError as exc:
        raise ValueError(
            "Filial inválida. Use 01 (Jaraguá do Sul/SC) ou 02 (Rio Bananal/ES)."
        ) from exc


def cost_center_scope_key(branch: str, code: str) -> tuple[str, str]:
    return (str(branch).strip(), str(code).strip())


def serialize_org_cost_center(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """Contrato público: filial + código + descrição (+ metadados internos)."""
    if not row:
        return None
    branch = str(row.get("branch") or row.get("unit_code") or "").strip()
    code = str(row.get("code") or "").strip()
    name = str(row.get("name") or "").strip()
    return {
        "id": row.get("id"),
        "branch": branch,
        "code": code,
        "description": name,
        "name": name,
        "unit_code": str(row.get("unit_code") or branch).strip(),
        "area_code": row.get("area_code"),
        "source": row.get("source") or COST_CENTER_SOURCE_MANUAL,
        "active": bool(row.get("active", True)),
        "created_at": row.get("created_at"),
        "created_by_user_id": row.get("created_by_user_id"),
    }
