"""Necessidade de material por bancada, com rateio FIFO do saldo compartilhado.

O saldo do Protheus é por produto e armazém, **não** por bancada. Se duas bancadas
consomem o mesmo componente, elas não podem ambas contar o mesmo saldo como já
disponível — a tela diria que está tudo coberto e o material faltaria na segunda.

O rateio é FIFO pelo início programado da operação: quem começa mais cedo consome
o saldo primeiro. Operação sem horário programado entra no fim da fila de rateio
(`line_feeder_schedule_cutoff.sort_by_scheduled_start`), porque não pode furar a
fila de quem tem horário definido.

Regra, por bancada e material elegível no corte:

    required_qty        = soma do saldo em aberto dos empenhos (D4_QUANT)
    point_of_use_qty    = parcela rateada do armazém 99 (ponto de uso)
    to_deliver_qty      = required_qty - point_of_use_qty
    source_available_qty = parcela rateada do armazém 01 (almoxarifado)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping

from production_control_app.domain.services.line_feeder_schedule_cutoff import (
    operation_scheduled_start,
    sort_by_scheduled_start,
)

# Tolerância de ponto flutuante: quantidade do Protheus vem com 6 decimais.
_EPSILON = 1e-6

# Alimentador coleta matéria-prima do almoxarifado; PI/PA ficam fora (produção).
# Espelha PRODUCT_TYPE_RAW_MATERIAL da api-delpi sem importar o domínio dela.
RAW_MATERIAL_PRODUCT_TYPE = "MP"

STATUS_COVERED = "covered"
STATUS_TO_PICK = "to_pick"
STATUS_AT_RISK = "at_risk"
# Saldo indisponível (api-delpi fora): não afirmar cobertura que não foi medida.
STATUS_UNKNOWN = "unknown"


@dataclass(frozen=True)
class MaterialRequirement:
    work_center: str
    product_code: str
    description: str
    unit: str
    required_qty: float
    point_of_use_qty: float | None
    to_deliver_qty: float | None
    source_available_qty: float | None
    status: str
    first_scheduled_at: str | None
    # OP/operação que precisa do material primeiro: é o prazo real do alimentador
    # e a referência estável do item na lista de coleta.
    first_production_order: str
    first_operation_code: str
    production_orders: tuple[str, ...]
    operation_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "work_center": self.work_center,
            "product_code": self.product_code,
            "description": self.description,
            "unit": self.unit,
            "required_qty": _round(self.required_qty),
            "point_of_use_qty": _round_optional(self.point_of_use_qty),
            "to_deliver_qty": _round_optional(self.to_deliver_qty),
            "source_available_qty": _round_optional(self.source_available_qty),
            "status": self.status,
            "first_scheduled_at": self.first_scheduled_at,
            "first_production_order": self.first_production_order,
            "first_operation_code": self.first_operation_code,
            "production_orders": list(self.production_orders),
            "operation_count": self.operation_count,
        }


@dataclass
class _DemandLine:
    work_center: str
    product_code: str
    description: str
    unit: str
    production_order: str
    operation_code: str
    scheduled_at: datetime | None
    required_qty: float
    point_of_use_qty: float = 0.0
    source_available_qty: float = 0.0

    @property
    def to_deliver_qty(self) -> float:
        return max(self.required_qty - self.point_of_use_qty, 0.0)


@dataclass
class _Aggregate:
    description: str = ""
    unit: str = ""
    required_qty: float = 0.0
    point_of_use_qty: float = 0.0
    source_available_qty: float = 0.0
    to_deliver_qty: float = 0.0
    first_scheduled_at: datetime | None = None
    first_production_order: str = ""
    first_operation_code: str = ""
    production_orders: list[str] = field(default_factory=list)
    operation_count: int = 0


def build_requirements(
    operations: Iterable[dict[str, Any]],
    *,
    commitments_by_operation: Mapping[tuple[str, str], list[dict[str, Any]]],
    point_of_use_balances: Mapping[str, float] | None,
    source_balances: Mapping[str, float] | None,
    balances_available: bool = True,
) -> list[MaterialRequirement]:
    """Necessidade por bancada e material, já rateada entre bancadas.

    ``commitments_by_operation`` é indexado por (OP, operação) normalizados.
    Com ``balances_available=False`` as quantidades de saldo voltam como ``None``
    e o status é ``unknown``: sem medir o saldo não se afirma cobertura.
    """
    lines = _demand_lines(operations, commitments_by_operation)
    if not lines:
        return []

    if balances_available:
        _allocate_fifo(lines, point_of_use_balances or {}, attribute="point_of_use_qty")
        _allocate_fifo(
            lines,
            source_balances or {},
            attribute="source_available_qty",
            demand_of=lambda line: line.to_deliver_qty,
        )

    return _aggregate(lines, balances_available=balances_available)


def _demand_lines(
    operations: Iterable[dict[str, Any]],
    commitments_by_operation: Mapping[tuple[str, str], list[dict[str, Any]]],
) -> list[_DemandLine]:
    lines: list[_DemandLine] = []
    for operation in sort_by_scheduled_start(list(operations)):
        work_center = _text(operation.get("work_center"))
        order = _text(operation.get("production_order"))
        operation_code = _text(operation.get("operation_code"))
        if not work_center or not order or not operation_code:
            continue
        materials = commitments_by_operation.get(
            (order, _normalize_operation_code(operation_code))
        )
        if not materials:
            continue
        scheduled_at = operation_scheduled_start(operation)
        for material in materials:
            product_code = _text(material.get("product_code"))
            required = _number(material.get("open_qty"))
            if not product_code or required <= _EPSILON:
                continue
            if not _is_raw_material(material.get("product_type")):
                continue
            lines.append(
                _DemandLine(
                    work_center=work_center,
                    product_code=product_code,
                    description=_text(material.get("description")),
                    unit=_text(material.get("unit")),
                    production_order=order,
                    operation_code=operation_code,
                    scheduled_at=scheduled_at,
                    required_qty=required,
                )
            )
    return lines


def _allocate_fifo(
    lines: list[_DemandLine],
    balances: Mapping[str, float],
    *,
    attribute: str,
    demand_of=lambda line: line.required_qty,
) -> None:
    """Consome o saldo do produto na ordem das linhas (já FIFO). Negativo = zero."""
    remaining: dict[str, float] = {}
    for line in lines:
        if line.product_code not in remaining:
            remaining[line.product_code] = max(
                _number(balances.get(line.product_code)), 0.0
            )
        demand = demand_of(line)
        if demand <= _EPSILON:
            continue
        allocated = min(remaining[line.product_code], demand)
        if allocated <= _EPSILON:
            continue
        remaining[line.product_code] -= allocated
        setattr(line, attribute, allocated)


def _aggregate(
    lines: list[_DemandLine],
    *,
    balances_available: bool,
) -> list[MaterialRequirement]:
    buckets: dict[tuple[str, str], _Aggregate] = {}
    for line in lines:
        key = (line.work_center, line.product_code)
        bucket = buckets.setdefault(key, _Aggregate())
        bucket.description = bucket.description or line.description
        bucket.unit = bucket.unit or line.unit
        # As linhas já chegam em ordem FIFO: a primeira do balde é a mais cedo.
        bucket.first_production_order = bucket.first_production_order or line.production_order
        bucket.first_operation_code = bucket.first_operation_code or line.operation_code
        bucket.required_qty += line.required_qty
        bucket.point_of_use_qty += line.point_of_use_qty
        bucket.source_available_qty += line.source_available_qty
        bucket.to_deliver_qty += line.to_deliver_qty
        bucket.operation_count += 1
        if line.production_order not in bucket.production_orders:
            bucket.production_orders.append(line.production_order)
        if line.scheduled_at is not None and (
            bucket.first_scheduled_at is None
            or line.scheduled_at < bucket.first_scheduled_at
        ):
            bucket.first_scheduled_at = line.scheduled_at

    requirements = [
        MaterialRequirement(
            work_center=work_center,
            product_code=product_code,
            description=bucket.description,
            unit=bucket.unit,
            required_qty=bucket.required_qty,
            point_of_use_qty=bucket.point_of_use_qty if balances_available else None,
            to_deliver_qty=bucket.to_deliver_qty if balances_available else None,
            source_available_qty=(
                bucket.source_available_qty if balances_available else None
            ),
            status=_status(bucket, balances_available=balances_available),
            first_scheduled_at=(
                bucket.first_scheduled_at.isoformat()
                if bucket.first_scheduled_at is not None
                else None
            ),
            first_production_order=bucket.first_production_order,
            first_operation_code=bucket.first_operation_code,
            production_orders=tuple(bucket.production_orders),
            operation_count=bucket.operation_count,
        )
        for (work_center, product_code), bucket in buckets.items()
    ]
    requirements.sort(key=_requirement_sort_key)
    return requirements


def _requirement_sort_key(item: MaterialRequirement) -> tuple[int, str, str, str]:
    return (
        _STATUS_PRIORITY.get(item.status, 9),
        item.work_center,
        item.first_scheduled_at or "9999-12-31T23:59:59",
        item.product_code,
    )


# O que pode faltar aparece antes do que já está coberto.
_STATUS_PRIORITY = {
    STATUS_AT_RISK: 0,
    STATUS_TO_PICK: 1,
    STATUS_UNKNOWN: 2,
    STATUS_COVERED: 3,
}


def _status(bucket: _Aggregate, *, balances_available: bool) -> str:
    if not balances_available:
        return STATUS_UNKNOWN
    if bucket.to_deliver_qty <= _EPSILON:
        return STATUS_COVERED
    if bucket.source_available_qty + _EPSILON >= bucket.to_deliver_qty:
        return STATUS_TO_PICK
    return STATUS_AT_RISK


def filter_requirements(
    requirements: list[MaterialRequirement],
    *,
    work_center: str | None = None,
    status: str | None = None,
) -> list[MaterialRequirement]:
    """Recorte de apresentação — aplicado **depois** do rateio.

    Filtrar antes mudaria a conta: uma bancada isolada pareceria dona de todo o
    saldo que na verdade divide com as outras.
    """
    center = _text(work_center)
    wanted = _text(status)
    return [
        item
        for item in requirements
        if (not center or item.work_center == center)
        and (not wanted or item.status == wanted)
    ]


def pick_list_candidates(
    requirements: list[MaterialRequirement],
) -> list[MaterialRequirement]:
    """Só entra na lista de coleta o que realmente falta na bancada."""
    return [
        item
        for item in requirements
        if item.to_deliver_qty is not None and item.to_deliver_qty > _EPSILON
    ]


@dataclass(frozen=True)
class ProductPickLine:
    """Item da lista de coleta: um produto, quantidade somada entre bancadas."""

    product_code: str
    description: str
    unit: str
    required_qty: float
    point_of_use_qty: float
    to_deliver_qty: float
    work_centers: tuple[str, ...]
    pickup_location: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "description": self.description,
            "unit": self.unit,
            "required_qty": _round(self.required_qty),
            "point_of_use_qty": _round(self.point_of_use_qty),
            "to_deliver_qty": _round(self.to_deliver_qty),
            "work_centers": list(self.work_centers),
            "pickup_location": self.pickup_location,
        }

    def with_pickup_location(self, location: str) -> "ProductPickLine":
        return ProductPickLine(
            product_code=self.product_code,
            description=self.description,
            unit=self.unit,
            required_qty=self.required_qty,
            point_of_use_qty=self.point_of_use_qty,
            to_deliver_qty=self.to_deliver_qty,
            work_centers=self.work_centers,
            pickup_location=_text(location),
        )


def pick_list_by_product(
    candidates: Iterable[MaterialRequirement],
) -> list[ProductPickLine]:
    """Colapsa a necessidade por produto para a lista de coleta do alimentador.

    Duas bancadas pedindo o mesmo componente viram uma linha: a quantidade a
    entregar é a soma. Ordenação por código do produto.
    """
    buckets: dict[str, _ProductBucket] = {}
    for item in candidates:
        code = _text(item.product_code)
        if not code:
            continue
        bucket = buckets.get(code)
        if bucket is None:
            bucket = _ProductBucket(
                description=_text(item.description),
                unit=_text(item.unit),
            )
            buckets[code] = bucket
        bucket.required_qty += float(item.required_qty or 0.0)
        bucket.point_of_use_qty += float(item.point_of_use_qty or 0.0)
        bucket.to_deliver_qty += float(item.to_deliver_qty or 0.0)
        center = _text(item.work_center)
        if center and center not in bucket.work_centers:
            bucket.work_centers.append(center)

    lines = [
        ProductPickLine(
            product_code=code,
            description=bucket.description,
            unit=bucket.unit,
            required_qty=_round(bucket.required_qty),
            point_of_use_qty=_round(bucket.point_of_use_qty),
            to_deliver_qty=_round(bucket.to_deliver_qty),
            work_centers=tuple(sorted(bucket.work_centers)),
        )
        for code, bucket in buckets.items()
        if bucket.to_deliver_qty > _EPSILON
    ]
    lines.sort(key=lambda line: line.product_code)
    return lines


@dataclass
class _ProductBucket:
    description: str
    unit: str
    required_qty: float = 0.0
    point_of_use_qty: float = 0.0
    to_deliver_qty: float = 0.0
    work_centers: list[str] = field(default_factory=list)


def summarize(requirements: list[MaterialRequirement]) -> dict[str, Any]:
    to_deliver = sum(
        item.to_deliver_qty or 0.0
        for item in requirements
        if item.status in (STATUS_TO_PICK, STATUS_AT_RISK)
    )
    return {
        "material_count": len(requirements),
        "work_center_count": len({item.work_center for item in requirements}),
        "covered_count": sum(
            1 for item in requirements if item.status == STATUS_COVERED
        ),
        "to_pick_count": sum(
            1 for item in requirements if item.status == STATUS_TO_PICK
        ),
        "at_risk_count": sum(
            1 for item in requirements if item.status == STATUS_AT_RISK
        ),
        "unknown_count": sum(
            1 for item in requirements if item.status == STATUS_UNKNOWN
        ),
        "to_deliver_qty": _round(to_deliver),
    }


def group_by_work_center(
    requirements: list[MaterialRequirement],
) -> list[dict[str, Any]]:
    """Agrupa por bancada preservando a ordem de risco de cada material."""
    groups: dict[str, list[MaterialRequirement]] = {}
    for item in requirements:
        groups.setdefault(item.work_center, []).append(item)

    payload: list[dict[str, Any]] = []
    for work_center, items in groups.items():
        payload.append(
            {
                "work_center": work_center,
                "summary": summarize(items),
                "items": [item.as_dict() for item in items],
            }
        )
    payload.sort(
        key=lambda group: (
            -group["summary"]["at_risk_count"],
            -group["summary"]["to_pick_count"],
            group["work_center"],
        )
    )
    return payload


def normalize_commitments(
    items: Iterable[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Indexa os empenhos da api-delpi por (OP, operação) normalizados."""
    indexed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in items:
        order = _text(item.get("production_order"))
        operation = _normalize_operation_code(item.get("operation"))
        if not order or not operation:
            continue
        indexed.setdefault((order, operation), []).append(item)
    return indexed


def _normalize_operation_code(value: Any) -> str:
    """``01`` e ``1`` são a mesma operação; o TOTVS não é consistente no zero à esquerda."""
    text = _text(value)
    if not text:
        return ""
    return text.lstrip("0") or "0"


def _is_raw_material(product_type: Any) -> bool:
    """Fail-closed: sem tipo cadastrado o alimentador não trata como MP."""
    return _text(product_type).upper() == RAW_MATERIAL_PRODUCT_TYPE


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _round(value: float) -> float:
    return round(float(value or 0), 6)


def _round_optional(value: float | None) -> float | None:
    return None if value is None else _round(value)
