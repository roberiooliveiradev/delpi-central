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
commitment_count``. Sem o campo (producer antigo) a prova falta — e prova
insuficiente nunca vira ``resolved``: o item fica ``indeterminate`` e a
operação sai ``incomplete``.

Regra de integridade (hardening): a elegibilidade de um item tem três estados
— ``eligible`` provado, ``ineligible`` provado, ``indeterminate`` (falta dado
que pode mudar a decisão). Qualquer item indeterminado no escopo avaliado
impede ``resolved``/``missing`` confiável → a operação vira ``incomplete``.
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

_ITEM_ELIGIBLE = "eligible"
_ITEM_INELIGIBLE = "ineligible"
_ITEM_INDETERMINATE = "indeterminate"


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
    """
    return _zeroed_state(item) == "zeroed"


def _zeroed_state(item: dict[str, Any]) -> str:
    """``zeroed`` provado / ``not_zeroed`` provado / ``unknown``.

    Campo ausente (producer antigo em convivência de versões): ``unknown``
    quando as quantidades agregadas são ambas zero — pode ser netting ou
    registros realmente zerados. Agregado não-zero prova ``not_zeroed``.
    Campo inválido (não numérico, negativo ou acima de ``commitment_count``)
    também é ``unknown`` — contagens inconsistentes não provam nada.
    """
    if "zeroed_commitment_count" not in item:
        if _number(item.get("original_qty")) != 0 or _number(item.get("open_qty")) != 0:
            return "not_zeroed"
        return "unknown"
    zeroed = _count(item.get("zeroed_commitment_count"))
    total = _count(item.get("commitment_count"))
    if zeroed is None or total is None or total <= 0 or zeroed < 0 or zeroed > total:
        return "unknown"
    return "zeroed" if zeroed >= total else "not_zeroed"


def _count(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != int(parsed):
        return None
    return int(parsed)


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _item_disposition(
    item: dict[str, Any],
    *,
    material_type: str,
    groups: set[str],
    ignore_zeroed: bool,
) -> str:
    """Elegibilidade provada do item para o critério material_code.

    ``ineligible`` exige prova (tipo conhecido ≠ MP, ou grupo conhecido fora
    da configuração). Dado indispensável ausente → ``indeterminate``: tipo
    vazio, MP sem grupo, elegível sem código de produto, ou contagem de
    zerados sem prova suficiente.
    """
    product_type = _text(item.get("product_type")).upper()
    if not product_type:
        return _ITEM_INDETERMINATE
    if product_type != material_type:
        return _ITEM_INELIGIBLE
    group = _text(item.get("product_group"))
    if not group:
        return _ITEM_INDETERMINATE
    if group not in groups:
        return _ITEM_INELIGIBLE
    if not _text(item.get("product_code")):
        return _ITEM_INDETERMINATE
    if ignore_zeroed:
        state = _zeroed_state(item)
        if state == "zeroed":
            return _ITEM_INELIGIBLE
        if state == "unknown":
            return _ITEM_INDETERMINATE
    return _ITEM_ELIGIBLE


def _classify_scope(
    items: list[dict[str, Any]],
    *,
    material_type: str,
    groups: set[str],
    ignore_zeroed: bool,
) -> tuple[list[str], dict[str, dict[str, Any]], int]:
    """Códigos elegíveis provados (ordenados) + evidência + nº indeterminados."""
    by_code: dict[str, dict[str, Any]] = {}
    indeterminate = 0
    for item in items:
        disposition = _item_disposition(
            item,
            material_type=material_type,
            groups=groups,
            ignore_zeroed=ignore_zeroed,
        )
        if disposition == _ITEM_INDETERMINATE:
            indeterminate += 1
            continue
        if disposition != _ITEM_ELIGIBLE:
            continue
        by_code.setdefault(_text(item.get("product_code")), item)
    return sorted(by_code), by_code, indeterminate


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


def _scope_result(
    identity: dict[str, str],
    items: list[dict[str, Any]],
    *,
    filters: dict[str, Any],
    source: str,
    resolved_detail: str,
    ambiguous_detail: str,
) -> dict[str, Any] | None:
    """Decisão de um escopo; ``None`` = nada elegível provado → escopo seguinte."""
    codes, by_code, indeterminate = _classify_scope(items, **filters)
    if len(codes) > 1:
        return _result(
            identity,
            status=RESOLUTION_AMBIGUOUS,
            candidate_codes=codes,
            detail=ambiguous_detail,
        )
    if indeterminate:
        return _result(
            identity,
            status=RESOLUTION_INCOMPLETE,
            candidate_codes=codes,
            detail="insufficient_material_data",
        )
    if codes:
        return _result(
            identity,
            status=RESOLUTION_RESOLVED,
            product_code=codes[0],
            product_group=_text(by_code[codes[0]].get("product_group")),
            source=source,
            candidate_codes=codes,
            detail=resolved_detail,
        )
    return None


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
    ``ambiguous``, zero é ``missing``, um é ``resolved`` — e nada disso vale
    se houver item ``indeterminate`` no escopo (→ ``incomplete``).
    """
    identity = operation_identity(operation)
    operation_code = _normalize_operation_code(identity["operation_code"])
    material_type = _text(params.get("material_type")).upper()
    groups = {_text(group) for group in params.get("eligible_product_groups") or ()}
    filters = {
        "material_type": material_type,
        "groups": groups,
        "ignore_zeroed": bool(params.get("ignore_zeroed_allocations", True)),
    }

    direct_items = [
        item
        for item in order_items
        if _normalize_operation_code(item.get("operation")) == operation_code
    ]
    direct = _scope_result(
        identity,
        direct_items,
        filters=filters,
        source=IDENTITY_DIRECT,
        resolved_detail="material_identified_at_operation",
        ambiguous_detail="multiple_eligible_materials_at_operation",
    )
    if direct is not None:
        return direct

    source = _text(params.get("identity_source")) or MATERIAL_SOURCE_OPERATION_THEN_ORDER
    if source != MATERIAL_SOURCE_OPERATION_THEN_ORDER:
        return _result(
            identity,
            status=RESOLUTION_MISSING,
            detail="identity_source_without_fallback",
        )

    fallback = _scope_result(
        identity,
        order_items,
        filters=filters,
        source=IDENTITY_FALLBACK_OP,
        resolved_detail="material_identified_at_order_fallback",
        ambiguous_detail="multiple_eligible_materials_at_order",
    )
    if fallback is not None:
        return fallback
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
