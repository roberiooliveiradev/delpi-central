from __future__ import annotations

from datetime import date, datetime
from typing import Any

# Campos de negócio que compõem o snapshot da revisão.
SNAPSHOT_FIELDS = (
    "branch_code",
    "title",
    "accountable",
    "sector",
    "investment",
    "savings_type",
    "seconds_per_occurrence",
    "occurrences_per_day",
    "hourly_cost",
    "quantity_saved_per_day",
    "unit_material_cost",
    "fixed_daily_savings",
    "daily_savings",
    "annual_savings",
    "status",
    "date_implemented",
    "date_discontinued",
    "notes",
    "process_description",
    "problem_description",
    "improvement_description",
    "expected_result",
    "category",
)

# Campos cujo valor, ao mudar, obriga a criação de uma nova revisão.
REVISION_TRIGGER_FIELDS = (
    "status",
    "date_implemented",
    "date_discontinued",
    "savings_type",
    "seconds_per_occurrence",
    "occurrences_per_day",
    "hourly_cost",
    "quantity_saved_per_day",
    "unit_material_cost",
    "fixed_daily_savings",
    "branch_code",
    "title",
)

_STATUS_LABELS = {
    "em_andamento": "Em andamento",
    "implantado": "Implantado",
    "descontinuado": "Descontinuado",
    "cancelado": "Cancelado",
}


def _normalize(value: Any) -> Any:
    """Normaliza valores para comparação estável (datas/decimais viram string/float)."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def changed_trigger_fields(current: dict[str, Any], updated: dict[str, Any]) -> list[str]:
    """Lista campos gatilho cujo valor mudou entre estado atual e novo."""
    changed: list[str] = []
    for field in REVISION_TRIGGER_FIELDS:
        if field not in updated:
            continue
        if _normalize(current.get(field)) != _normalize(updated.get(field)):
            changed.append(field)
    return changed


def resolve_change_type(
    current: dict[str, Any] | None,
    merged: dict[str, Any],
    *,
    is_creation: bool,
) -> str:
    """Determina o tipo semântico da mudança (transformômetro-like)."""
    new_status = _normalize(merged.get("status"))

    if is_creation:
        return "implantacao" if new_status == "implantado" else "baseline"

    old_status = _normalize((current or {}).get("status"))
    if new_status != old_status:
        if new_status == "implantado":
            return "implantacao"
        if new_status == "descontinuado":
            return "descontinuacao"
    return "melhoria"


def build_change_summary(
    current: dict[str, Any] | None,
    merged: dict[str, Any],
    changed_fields: list[str],
) -> str | None:
    """Resumo curto e legível da mudança (ex.: 'status: Em andamento → Implantado')."""
    if current is None:
        return None
    if "status" in changed_fields:
        old = _STATUS_LABELS.get(_normalize(current.get("status")) or "", current.get("status"))
        new = _STATUS_LABELS.get(_normalize(merged.get("status")) or "", merged.get("status"))
        return f"status: {old} → {new}"
    if changed_fields:
        return "economia atualizada" if any(
            f not in ("status", "title", "branch_code") for f in changed_fields
        ) else "identificação atualizada"
    return None


def build_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    """Extrai apenas os campos de negócio do registro para o snapshot JSONB."""
    return {field: _normalize(record.get(field)) for field in SNAPSHOT_FIELDS}


def resolve_effective_from(
    merged: dict[str, Any],
    *,
    provided: str | None = None,
) -> str:
    """Data de início de vigência da nova revisão."""
    if provided:
        return provided
    implemented = merged.get("date_implemented")
    normalized = _normalize(implemented)
    if isinstance(normalized, str) and normalized:
        return normalized
    return date.today().isoformat()
