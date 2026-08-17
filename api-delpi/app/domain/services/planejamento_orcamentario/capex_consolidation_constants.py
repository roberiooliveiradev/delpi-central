"""Constantes — consolidação gerencial CAPEX (Fase 2D.1)."""

from __future__ import annotations

ENTITY_TYPE_CAPEX_CONSOLIDATION = "capex_consolidation"

AUDIT_CONSOLIDATION_SUMMARY = "capex_consolidation.summary_viewed"
AUDIT_CONSOLIDATION_EXPORT = "capex_consolidation.exported"

DEFAULT_CURRENCY = "BRL"

GROUP_BY_UNIT = "unit"
GROUP_BY_AREA = "area"
GROUP_BY_COST_CENTER = "cost_center"
GROUP_BY_CATEGORY = "category"
GROUP_BY_PRIORITY = "priority"
GROUP_BY_ORIGIN = "origin"
GROUP_BY_MONTH = "month"
GROUP_BY_PLAN_STATUS = "plan_status"

ALLOWED_GROUP_BY = frozenset(
    {
        GROUP_BY_UNIT,
        GROUP_BY_AREA,
        GROUP_BY_COST_CENTER,
        GROUP_BY_CATEGORY,
        GROUP_BY_PRIORITY,
        GROUP_BY_ORIGIN,
        GROUP_BY_MONTH,
        GROUP_BY_PLAN_STATUS,
    }
)

# Ordenação segura do detalhamento gerencial
DETAILS_SORT_FIELDS = frozenset(
    {
        "cost_center_id",
        "unit_id",
        "area_id",
        "description",
        "estimated_amount",
        "required_date",
        "priority",
        "origin",
        "plan_status",
        "updated_at",
        "created_at",
    }
)

PRIORITY_LABELS = {
    "1": "Alta",  # legado planilha (compra aprovada)
    "2": "Alta",
    "3": "Média",
    "4": "Baixa",
}

ORIGIN_LABELS = {
    "national": "Nacional",
    "imported": "Importado",
}

PLAN_STATUS_LABELS = {
    "draft": "Rascunho",
    "submitted": "Enviado para aprovação",
    "changes_requested": "Ajustes solicitados",
    "rejected": "Reprovado",
    "approved": "Aprovado",
}
