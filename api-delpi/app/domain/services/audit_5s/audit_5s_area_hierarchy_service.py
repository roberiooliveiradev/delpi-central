"""Regras de hierarquia de áreas 5S (agregadora → subáreas, profundidade 1)."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

HIERARCHY_WRITE_BRANCH = "02"

AGGREGATOR_NOT_AUDITABLE_MESSAGE = (
    "Área agregadora não pode receber auditoria. Selecione uma subárea ou área folha."
)
HIERARCHY_BRANCH_FORBIDDEN_MESSAGE = (
    "Hierarquia de áreas 5S só é permitida na filial 02."
)
PARENT_HAS_AUDITS_MESSAGE = (
    "Não é possível vincular subáreas a uma área que já possui auditorias. "
    "Crie uma área agregadora nova."
)
PARENT_IS_SUB_AREA_MESSAGE = "Uma subárea não pode ser área agregadora."
CHILD_IS_AGGREGATOR_MESSAGE = "Uma área agregadora não pode ser vinculada como subárea."
CHILD_BRANCH_MISMATCH_MESSAGE = "Subárea deve pertencer à mesma filial da agregadora."
CHILD_SELF_MESSAGE = "Área agregadora não pode ser vinculada a si mesma."
PARENT_NOT_FOUND_MESSAGE = "Área agregadora não encontrada."
CHILD_NOT_FOUND_MESSAGE = "Uma ou mais subáreas não foram encontradas."


class Audit5sAreaHierarchyError(ValueError):
    """Violação de regra de hierarquia de áreas 5S."""


def is_hierarchy_write_allowed(branch_code: str | None) -> bool:
    return str(branch_code or "").strip() == HIERARCHY_WRITE_BRANCH


def require_hierarchy_write_branch(branch_code: str | None) -> None:
    if not is_hierarchy_write_allowed(branch_code):
        raise Audit5sAreaHierarchyError(HIERARCHY_BRANCH_FORBIDDEN_MESSAGE)


def children_count(area: dict[str, Any] | None) -> int:
    if not area:
        return 0
    raw = area.get("children_count")
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def is_aggregator(area: dict[str, Any] | None) -> bool:
    return children_count(area) > 0


def is_sub_area(area: dict[str, Any] | None) -> bool:
    if not area:
        return False
    parent_id = area.get("parent_area_id")
    return parent_id is not None and str(parent_id).strip() != ""


def is_leaf(area: dict[str, Any] | None) -> bool:
    """Folha auditável: não tem filhos (pode ou não ter pai)."""
    return not is_aggregator(area)


def enrich_area_hierarchy_fields(area: dict[str, Any]) -> dict[str, Any]:
    out = dict(area)
    count = children_count(out)
    out["children_count"] = count
    out["is_aggregator"] = count > 0
    out["is_sub_area"] = is_sub_area(out)
    parent_id = out.get("parent_area_id")
    if parent_id is not None:
        out["parent_area_id"] = str(parent_id)
    return out


def assert_area_auditable(area: dict[str, Any] | None) -> None:
    if area is None:
        raise Audit5sAreaHierarchyError("Área auditada não encontrada.")
    if is_aggregator(area):
        raise Audit5sAreaHierarchyError(AGGREGATOR_NOT_AUDITABLE_MESSAGE)


def _area_id(area: dict[str, Any]) -> str:
    return str(area.get("id") or "").strip()


def validate_set_children(
    *,
    parent: dict[str, Any] | None,
    children: Sequence[dict[str, Any]],
    child_ids: Sequence[str],
    parent_audit_count: int,
) -> list[str]:
    """
    Valida substituição do conjunto de filhos de uma agregadora.

    Retorna a lista normalizada de child_ids (únicos, ordem preservada).
    """
    if parent is None:
        raise Audit5sAreaHierarchyError(PARENT_NOT_FOUND_MESSAGE)

    require_hierarchy_write_branch(str(parent.get("branch_code") or ""))

    if is_sub_area(parent):
        raise Audit5sAreaHierarchyError(PARENT_IS_SUB_AREA_MESSAGE)

    if int(parent_audit_count or 0) > 0:
        raise Audit5sAreaHierarchyError(PARENT_HAS_AUDITS_MESSAGE)

    parent_id = _area_id(parent)
    parent_branch = str(parent.get("branch_code") or "").strip()

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in child_ids:
        cid = str(raw or "").strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        normalized.append(cid)

    if len(normalized) != len({str(c.get("id") or "").strip() for c in children}):
        raise Audit5sAreaHierarchyError(CHILD_NOT_FOUND_MESSAGE)

    by_id = {_area_id(c): c for c in children}
    for cid in normalized:
        if cid == parent_id:
            raise Audit5sAreaHierarchyError(CHILD_SELF_MESSAGE)
        child = by_id.get(cid)
        if child is None:
            raise Audit5sAreaHierarchyError(CHILD_NOT_FOUND_MESSAGE)
        if str(child.get("branch_code") or "").strip() != parent_branch:
            raise Audit5sAreaHierarchyError(CHILD_BRANCH_MISMATCH_MESSAGE)
        if is_aggregator(child):
            raise Audit5sAreaHierarchyError(CHILD_IS_AGGREGATOR_MESSAGE)

    return normalized


def mean_of_means(values: Iterable[float | int | None]) -> float | None:
    """Média aritmética das médias; ignora None / vazios."""
    nums: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            nums.append(float(value))
        except (TypeError, ValueError):
            continue
    if not nums:
        return None
    return round(sum(nums) / len(nums), 2)


def eligible_child_candidates(
    areas: Sequence[dict[str, Any]],
    *,
    parent_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Áreas elegíveis a subárea: não agregadoras; se já são subárea de outro pai,
    ainda podem ser listadas para remapeamento (a UI decide).
    Filhas atuais do parent_id sempre entram.
    """
    result: list[dict[str, Any]] = []
    parent = str(parent_id or "").strip() or None
    for area in areas:
        enriched = enrich_area_hierarchy_fields(dict(area))
        if enriched["is_aggregator"] and _area_id(enriched) != parent:
            continue
        if enriched["is_aggregator"]:
            continue
        result.append(enriched)
    return result
