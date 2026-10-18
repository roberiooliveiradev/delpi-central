"""Resolução do código de material de cada operação — Regras de Sequenciamento E2.

Camada pura de classificação: recebe os itens de empenho já normalizados pela
api-delpi (contrato ``operation-materials``) e os parâmetros validados do
critério ``material_code`` do perfil, e decide o status de cada operação. Não
faz I/O, não chama rede e não toca fila/snapshot — quem busca os dados é o
serviço de aplicação, quem ordena continua sendo o motor vigente.

Semântica de "registro zerado": o agregado ``original_qty``/``open_qty`` pode
zerar por soma de positivos e negativos. Por isso o contrato expõe
``zeroed_commitment_count`` (registros fonte com as duas quantidades zero):
o item só é "totalmente zerado" quando ``zeroed_commitment_count ==
commitment_count``. Sem o campo (producer antigo) o item NÃO é tratado como
zerado — manter o item elegível falha para ambiguidade, nunca para descarte
silencioso.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.sequencing_profile import (
    CRITERION_MATERIAL_CODE,
    MATERIAL_SOURCE_OPERATION_THEN_ORDER,
)
from production_control_app.domain.services.line_feeder_requirements import (
    _normalize_operation_code,
)
from production_control_app.domain.services.production_order_key import (
    normalize_order_code,
)

RESOLUTION_RESOLVED = "resolved"
RESOLUTION_MISSING = "missing"
RESOLUTION_AMBIGUOUS = "ambiguous"
RESOLUTION_SOURCE_UNAVAILABLE = "source_unavailable"
RESOLUTION_INCOMPLETE = "incomplete"
RESOLUTION_STATUSES: frozenset[str] = frozenset(
    {
        RESOLUTION_RESOLVED,
        RESOLUTION_MISSING,
        RESOLUTION_AMBIGUOUS,
        RESOLUTION_SOURCE_UNAVAILABLE,
        RESOLUTION_INCOMPLETE,
    }
)

IDENTITY_DIRECT = "direct"
IDENTITY_FALLBACK_OP = "fallback_op"


def material_criterion_params(criteria: Any) -> dict[str, Any] | None:
    """Extrai os params já validados do critério ``material_code``, se existir.

    O perfil é persistido validado por ``validate_criteria``; aqui só procuramos
    o critério na lista normalizada. ``None`` = perfil não usa material_code,
    e o chamador decide se a resolução se aplica.
    """
    if not isinstance(criteria, list):
        return None
    for criterion in criteria:
        if isinstance(criterion, dict) and criterion.get("type") == CRITERION_MATERIAL_CODE:
            params = criterion.get("params")
            return params if isinstance(params, dict) else None
    return None


def operation_identity(item: dict[str, Any]) -> dict[str, str]:
    """Identidade completa da operação na fila: filial + CT atual + OP + operação."""
    return {
        "branch": _text(item.get("branch")),
        "work_center": _text(item.get("work_center")),
        "production_order": normalize_order_code(item.get("production_order")),
        "operation_code": _text(item.get("operation_code")),
    }


def is_fully_zeroed(item: dict[str, Any]) -> bool:
    """True só quando TODOS os registros fonte do item têm as duas quantidades zero.

    ``zeroed_commitment_count`` é a prova canônica (ver docstring do módulo).
    Sem o campo — producer sem a evolução de contrato — a resposta conservadora
    é ``False``: manter elegível pode flagar AMBIGUOUS, descartar poderia
    esconder o único cabo real da operação.
    """
    if "zeroed_commitment_count" not in item:
        return False
    try:
        zeroed = int(item.get("zeroed_commitment_count") or 0)
        total = int(item.get("commitment_count") or 0)
    except (TypeError, ValueError):
        return False
    return total > 0 and zeroed >= total


def _is_eligible(item: dict[str, Any], *, material_type: str, groups: set[str]) -> bool:
    """Fail-closed: sem tipo/grupo cadastrado o item não é cabo elegível."""
    if _text(item.get("product_type")).upper() != material_type:
        return False
    return _text(item.get("product_group")) in groups


def _eligible_codes(
    items: list[dict[str, Any]],
    *,
    material_type: str,
    groups: set[str],
    ignore_zeroed: bool,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Códigos distintos elegíveis (ordenados) + evidência por código."""
    by_code: dict[str, dict[str, Any]] = {}
    for item in items:
        if not _is_eligible(item, material_type=material_type, groups=groups):
            continue
        if ignore_zeroed and is_fully_zeroed(item):
            continue
        code = _text(item.get("product_code"))
        if not code:
            continue
        by_code.setdefault(code, item)
    return sorted(by_code), by_code


def _result(
    identity: dict[str, str],
    *,
    status: str,
    product_code: str | None = None,
    product_group: str | None = None,
    source: str | None = None,
    candidate_codes: list[str] | None = None,
    detail: str = "",
) -> dict[str, Any]:
    return {
        **identity,
        "status": status,
        "product_code": product_code,
        "product_group": product_group,
        "source": source,
        "candidate_codes": candidate_codes or [],
        "detail": detail,
    }


def resolve_operation_material(
    *,
    operation: dict[str, Any],
    order_items: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Classifica uma operação da fila contra os empenhos da sua OP.

    ``order_items`` são TODOS os itens de empenho da OP na filial (contrato
    batch: cada item já traz ``operation`` e ``product_code`` normalizados).
    A operação primeiro tenta o vínculo direto OP+operação; sem código elegível
    cai para a OP inteira conforme ``identity_source``.

    Nunca escolhe entre candidatos: 2+ códigos distintos elegíveis é
    ``ambiguous``, zero é ``missing``, um é ``resolved``.
    """
    identity = operation_identity(operation)
    operation_code = _normalize_operation_code(identity["operation_code"])
    material_type = _text(params.get("material_type")).upper()
    groups = {_text(group) for group in params.get("eligible_product_groups") or ()}
    ignore_zeroed = bool(params.get("ignore_zeroed_allocations", True))
    filters = {
        "material_type": material_type,
        "groups": groups,
        "ignore_zeroed": ignore_zeroed,
    }

    direct_items = [
        item
        for item in order_items
        if _normalize_operation_code(item.get("operation")) == operation_code
    ]
    codes, by_code = _eligible_codes(direct_items, **filters)
    if len(codes) == 1:
        return _result(
            identity,
            status=RESOLUTION_RESOLVED,
            product_code=codes[0],
            product_group=_text(by_code[codes[0]].get("product_group")),
            source=IDENTITY_DIRECT,
            candidate_codes=codes,
            detail="material_identified_at_operation",
        )
    if len(codes) > 1:
        return _result(
            identity,
            status=RESOLUTION_AMBIGUOUS,
            candidate_codes=codes,
            detail="multiple_eligible_materials_at_operation",
        )

    source = _text(params.get("identity_source")) or MATERIAL_SOURCE_OPERATION_THEN_ORDER
    if source != MATERIAL_SOURCE_OPERATION_THEN_ORDER:
        return _result(
            identity,
            status=RESOLUTION_MISSING,
            detail="identity_source_without_fallback",
        )

    codes, by_code = _eligible_codes(order_items, **filters)
    if len(codes) == 1:
        return _result(
            identity,
            status=RESOLUTION_RESOLVED,
            product_code=codes[0],
            product_group=_text(by_code[codes[0]].get("product_group")),
            source=IDENTITY_FALLBACK_OP,
            candidate_codes=codes,
            detail="material_identified_at_order_fallback",
        )
    if len(codes) > 1:
        return _result(
            identity,
            status=RESOLUTION_AMBIGUOUS,
            candidate_codes=codes,
            detail="multiple_eligible_materials_at_order",
        )
    return _result(identity, status=RESOLUTION_MISSING, detail="no_eligible_material")


def resolve_operations_materials(
    *,
    operations: list[dict[str, Any]],
    items_by_order: dict[str, list[dict[str, Any]]],
    params: dict[str, Any],
    unavailable_orders: set[str] | None = None,
    incomplete_orders: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Classifica a lista inteira; determinística na ordem de ``operations``.

    OPs marcadas indisponíveis/incompletas pelo fetch não vão para
    ``missing``: falha de integração nunca é ausência real de cabo.
    """
    unavailable = unavailable_orders or set()
    incomplete = incomplete_orders or set()
    results: list[dict[str, Any]] = []
    for operation in operations:
        order = normalize_order_code(operation.get("production_order"))
        if order in unavailable:
            results.append(
                _result(
                    operation_identity(operation),
                    status=RESOLUTION_SOURCE_UNAVAILABLE,
                    detail="materials_source_unavailable",
                )
            )
            continue
        if order in incomplete:
            results.append(
                _result(
                    operation_identity(operation),
                    status=RESOLUTION_INCOMPLETE,
                    detail="materials_response_incomplete",
                )
            )
            continue
        results.append(
            resolve_operation_material(
                operation=operation,
                order_items=items_by_order.get(order, []),
                params=params,
            )
        )
    return results


def _text(value: Any) -> str:
    return str(value or "").strip()
