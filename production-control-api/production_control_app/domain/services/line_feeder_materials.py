"""Motor puro — necessidade dinâmica de materiais do Alimentador (Etapa 3).

Fórmula canônica (por material, saldo compartilhado da fábrica):

``to_collect = max(0, required_from_horizon - factory_available)``

O saldo do ponto de uso (armazém 99) é descontado **uma única vez** na
consolidação global. O almoxarifado (01) é apenas informativo.

Seleção de operações: horizonte de horas (coberta total ou parcial).

Demanda de material (decisão de negócio vigente):

``material_needed = open_qty``  (saldo SD4 aberto da operação contemplada)

Não há proporcionalidade ``covered_qty / pending_qty`` sobre o empenho.
``origins[].fraction`` permanece como **razão informativa de cobertura do
horizonte** (``covered_qty / pending_qty``); ``required_qty`` da origem é o
empenho aberto integral (``demand_basis = open_commitment``).

Não usa SG1, listas anteriores, status de coleta nem ``original_qty``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Mapping, Sequence

from production_control_app.domain.services.line_feeder_requirements import (
    RAW_MATERIAL_PRODUCT_TYPE,
)

_EPSILON = Decimal("1e-9")
_QTY_PLACES = Decimal("0.000001")

STATUS_COVERED = "covered"
STATUS_TO_PICK = "to_pick"
STATUS_AT_RISK = "at_risk"
STATUS_UNKNOWN = "unknown"

DEMAND_BASIS_OPEN_COMMITMENT = "open_commitment"


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return number


def _text(value: Any) -> str:
    return str(value or "").strip()


def _round_qty(value: Decimal) -> float:
    return float(value.quantize(_QTY_PLACES, rounding=ROUND_HALF_UP))


def _is_raw_material(product_type: Any) -> bool:
    return _text(product_type).upper() == RAW_MATERIAL_PRODUCT_TYPE


def _normalize_operation_code(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""
    return text.lstrip("0") or "0"


@dataclass(frozen=True, slots=True)
class CoveredOperationDemand:
    """Operação contemplada pelo horizonte (unidades operacionais)."""

    work_center: str
    work_center_name: str
    production_order: str
    operation_code: str
    operation_id: str
    sequence_position: int
    covered_qty: Decimal
    pending_qty: Decimal


@dataclass(frozen=True, slots=True)
class MaterialOriginLine:
    work_center: str
    production_order: str
    operation_code: str
    operation_id: str
    sequence_position: int
    covered_qty: float
    pending_qty: float
    open_qty: float
    fraction: float
    required_qty: float
    demand_basis: str = DEMAND_BASIS_OPEN_COMMITMENT


@dataclass
class _MaterialBucket:
    product_code: str
    description: str = ""
    unit: str = ""
    required_qty: Decimal = field(default_factory=lambda: Decimal("0"))
    origins: list[MaterialOriginLine] = field(default_factory=list)
    work_centers: list[str] = field(default_factory=list)


def commitment_material_qty(*, open_qty: Decimal) -> Decimal | None:
    """Demanda = saldo SD4 aberto. None só se o valor for inválido."""
    if open_qty < 0:
        return None
    if open_qty <= _EPSILON:
        return Decimal("0")
    return open_qty


def proportional_material_qty(
    *,
    open_qty: Decimal,
    covered_qty: Decimal,
    pending_qty: Decimal,
) -> Decimal | None:
    """Compat: antigos callers de teste. Preferir ``commitment_material_qty``.

    Mantido apenas como utilitário de cobertura informativa; **não** é a regra
    de demanda do Alimentador.
    """
    _ = (covered_qty, pending_qty)
    return commitment_material_qty(open_qty=open_qty)


def _coverage_fraction(covered_qty: Decimal, pending_qty: Decimal) -> Decimal:
    """Razão informativa covered/pending (clamp 0..1); não define required_qty."""
    if pending_qty <= _EPSILON:
        return Decimal("0")
    if covered_qty < 0:
        return Decimal("0")
    fraction = covered_qty / pending_qty
    if fraction < 0:
        return Decimal("0")
    if fraction > 1:
        return Decimal("1")
    return fraction


def build_material_demands(
    operations: Sequence[CoveredOperationDemand],
    commitments_by_operation: Mapping[tuple[str, str], list[dict[str, Any]]],
) -> tuple[list[_MaterialBucket], list[dict[str, Any]], bool]:
    """Agrega demanda por (produto, unidade) com empenho SD4 integral.

    Retorna (buckets, avisos, demands_ok).
    ``demands_ok=False`` quando alguma linha de empenho for semanticamente inválida.
    """
    buckets: dict[tuple[str, str], _MaterialBucket] = {}
    warnings: list[dict[str, Any]] = []
    demands_ok = True
    # Evita duplicar o mesmo empenho se a mesma OP/operação aparecer 2× no horizonte.
    seen_ops: set[tuple[str, str]] = set()

    for op in operations:
        if op.covered_qty <= _EPSILON:
            continue
        op_key = (op.production_order, _normalize_operation_code(op.operation_code))
        if op_key in seen_ops:
            warnings.append(
                {
                    "code": "duplicate_contemplated_operation_skipped",
                    "production_order": op.production_order,
                    "operation_code": op.operation_code,
                    "work_center": op.work_center,
                }
            )
            continue
        seen_ops.add(op_key)
        materials = commitments_by_operation.get(op_key) or []
        if not materials:
            warnings.append(
                {
                    "code": "no_commitments",
                    "production_order": op.production_order,
                    "operation_code": op.operation_code,
                    "work_center": op.work_center,
                }
            )
            continue
        coverage_fraction = _coverage_fraction(op.covered_qty, op.pending_qty)
        for material in materials:
            product_code = _text(material.get("product_code"))
            if not product_code:
                continue
            if not _is_raw_material(material.get("product_type")):
                continue
            open_qty = _dec(material.get("open_qty"))
            if open_qty is None:
                demands_ok = False
                warnings.append(
                    {
                        "code": "commitment_open_qty_invalid",
                        "product_code": product_code,
                        "production_order": op.production_order,
                        "operation_code": op.operation_code,
                    }
                )
                continue
            needed = commitment_material_qty(open_qty=open_qty)
            if needed is None:
                demands_ok = False
                warnings.append(
                    {
                        "code": "commitment_open_qty_invalid",
                        "product_code": product_code,
                        "production_order": op.production_order,
                        "operation_code": op.operation_code,
                    }
                )
                continue
            if needed <= _EPSILON:
                continue
            unit = _text(material.get("unit"))
            bucket_key = (product_code, unit)
            bucket = buckets.get(bucket_key)
            if bucket is None:
                bucket = _MaterialBucket(
                    product_code=product_code,
                    description=_text(material.get("description")),
                    unit=unit,
                )
                buckets[bucket_key] = bucket
            bucket.required_qty += needed
            if not bucket.description:
                bucket.description = _text(material.get("description"))
            if op.work_center and op.work_center not in bucket.work_centers:
                bucket.work_centers.append(op.work_center)
            bucket.origins.append(
                MaterialOriginLine(
                    work_center=op.work_center,
                    production_order=op.production_order,
                    operation_code=op.operation_code,
                    operation_id=op.operation_id,
                    sequence_position=op.sequence_position,
                    covered_qty=_round_qty(op.covered_qty),
                    pending_qty=_round_qty(op.pending_qty),
                    open_qty=_round_qty(open_qty),
                    fraction=_round_qty(coverage_fraction),
                    required_qty=_round_qty(needed),
                    demand_basis=DEMAND_BASIS_OPEN_COMMITMENT,
                )
            )

    result_buckets = [
        buckets[key] for key in sorted(buckets.keys(), key=lambda item: (item[0], item[1]))
    ]
    return result_buckets, warnings, demands_ok


def apply_factory_stock(
    buckets: Sequence[_MaterialBucket],
    *,
    factory_balances: Mapping[str, float] | None,
    source_balances: Mapping[str, float] | None,
    balances_available: bool,
) -> list[dict[str, Any]]:
    """Desconta o saldo da fábrica **uma vez** por produto consolidado."""
    items: list[dict[str, Any]] = []
    for bucket in buckets:
        product_code = bucket.product_code
        required = bucket.required_qty
        if not balances_available or factory_balances is None:
            factory_qty = None
            to_collect = None
            source_qty = None
            status = STATUS_UNKNOWN
        else:
            raw_factory = _dec(factory_balances.get(product_code))
            # Ausência no mapa, após consulta completa filtrada por códigos = zero.
            factory_available = (
                Decimal("0")
                if raw_factory is None
                else max(raw_factory, Decimal("0"))
            )
            factory_qty = _round_qty(factory_available)
            to_collect_dec = max(required - factory_available, Decimal("0"))
            to_collect = _round_qty(to_collect_dec)
            if source_balances is None:
                source_qty = None
            else:
                raw_source = _dec(source_balances.get(product_code))
                source_available = (
                    Decimal("0")
                    if raw_source is None
                    else max(raw_source, Decimal("0"))
                )
                source_qty = _round_qty(source_available)
            if to_collect_dec <= _EPSILON:
                status = STATUS_COVERED
            elif source_qty is not None and Decimal(str(source_qty)) + _EPSILON >= to_collect_dec:
                status = STATUS_TO_PICK
            elif source_qty is None:
                status = STATUS_TO_PICK
            else:
                status = STATUS_AT_RISK

        items.append(
            {
                "product_code": product_code,
                "description": bucket.description,
                "unit": bucket.unit,
                "required_qty": _round_qty(required),
                "factory_available_qty": factory_qty,
                "to_collect_qty": to_collect,
                "source_available_qty": source_qty,
                "point_of_use_warehouse": "99",
                "source_warehouse": "01",
                "status": status,
                "work_centers": list(bucket.work_centers),
                "origins": [
                    {
                        "work_center": origin.work_center,
                        "production_order": origin.production_order,
                        "operation_code": origin.operation_code,
                        "operation_id": origin.operation_id,
                        "sequence_position": origin.sequence_position,
                        "covered_qty": origin.covered_qty,
                        "pending_qty": origin.pending_qty,
                        "open_qty": origin.open_qty,
                        # Informativo: cobertura temporal do horizonte (≠ fator de demanda).
                        "fraction": origin.fraction,
                        "required_qty": origin.required_qty,
                        "demand_basis": origin.demand_basis,
                    }
                    for origin in bucket.origins
                ],
            }
        )
    return items


def summarize_materials(items: Sequence[dict[str, Any]]) -> dict[str, Any]:
    to_collect_total = sum(
        float(item.get("to_collect_qty") or 0.0)
        for item in items
        if item.get("status") in (STATUS_TO_PICK, STATUS_AT_RISK)
    )
    return {
        "material_count": len(items),
        "covered_count": sum(1 for item in items if item.get("status") == STATUS_COVERED),
        "to_pick_count": sum(1 for item in items if item.get("status") == STATUS_TO_PICK),
        "at_risk_count": sum(1 for item in items if item.get("status") == STATUS_AT_RISK),
        "unknown_count": sum(1 for item in items if item.get("status") == STATUS_UNKNOWN),
        "to_collect_qty": _round_qty(Decimal(str(to_collect_total))),
    }
