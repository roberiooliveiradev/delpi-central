"""Pendências de inclusão de OP, derivadas da cobertura canônica da Demanda.

Sem outro cálculo de estoque/OP: usa somente uncovered_quantity já alocado pelo
DemandCoverageService no snapshot autorizado. Agrupa por (filial, produto) e
separa as necessidades por vencimento para não antecipar toda a produção.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from production_control_app.domain.services.demand_coverage_service import DemandLine

_QTY_EPS = Decimal("0.000001")
_FAR_FUTURE = date.max
_KNOWN_UNITS = {"MI", "PC", "UN"}


def _decimal(value: float) -> Decimal:
    return Decimal(str(value))


def _to_pieces(quantity: Decimal, unit: str) -> int | None:
    """Converte só unidades conhecidas; sem presumir MI para campos vazios."""
    if unit not in _KNOWN_UNITS:
        return None
    pieces = quantity * (1000 if unit == "MI" else 1)
    return int(pieces.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _recommended_date(due: date | None, today: date) -> str | None:
    if due is None:
        return None
    # Nunca sugerir data retroativa, inclusive entregas amanhã/hoje.
    return max(today, due - timedelta(days=2)).isoformat()


def build_op_pendencies(
    lines: Iterable[DemandLine],
    *,
    branch: str,
    today: date,
    incomplete_products: set[str] | None = None,
) -> dict[str, Any]:
    """Uma pendência por produto, cronologia completa e primeira data acionável."""
    excluded_products = incomplete_products or set()
    grouped: dict[str, list[DemandLine]] = defaultdict(list)
    suppressed: set[str] = set(excluded_products)
    for line in lines:
        if line.branch != branch or not line.product_code:
            continue
        if _decimal(line.uncovered_quantity) > _QTY_EPS:
            if line.op_coverage_incomplete:
                suppressed.add(line.product_code)
            grouped[line.product_code].append(line)

    result: list[dict[str, Any]] = []
    for product, product_lines in grouped.items():
        # Se a unidade/saldo da OP é incerto, nunca criar alarme de nova OP
        # como se a falta fosse confirmada.
        if product in suppressed:
            continue
        units = {line.unit.strip().upper() or "UNSPECIFIED" for line in product_lines}
        if len(units) > 1:
            suppressed.add(product)
            continue
        unit = next(iter(units), "UNSPECIFIED")
        ordered = sorted(
            product_lines,
            key=lambda line: (
                line.due_date or _FAR_FUTURE,
                line.source,
                line.sales_order,
                line.line_item,
            ),
        )
        by_due: dict[date | None, list[DemandLine]] = defaultdict(list)
        for line in ordered:
            by_due[line.due_date].append(line)

        schedule: list[dict[str, Any]] = []
        for due in sorted(by_due, key=lambda d: d or _FAR_FUTURE):
            group = by_due[due]
            qty = sum((_decimal(line.uncovered_quantity) for line in group), Decimal(0))
            schedule.append({
                "required_date": due.isoformat() if due else None,
                "suggested_op_date": _recommended_date(due, today),
                "uncovered_quantity": float(qty.quantize(Decimal("0.001"))),
                "uncovered_pieces": _to_pieces(qty, unit),
                "demand_count": len(group),
                "lines": [line.to_dict(today) for line in group],
            })

        if not schedule:
            continue
        total = sum((_decimal(line.uncovered_quantity) for line in ordered), Decimal(0))
        first = schedule[0]
        result.append({
            "id": f"{branch}|include-production-order|{product}",
            "kind": "include_production_order",
            "branch": branch,
            "product_code": product,
            "unit": unit,
            "required_date": first["required_date"],
            "suggested_op_date": first["suggested_op_date"],
            "next_uncovered_quantity": first["uncovered_quantity"],
            "next_uncovered_pieces": first["uncovered_pieces"],
            "total_uncovered_quantity": float(total.quantize(Decimal("0.001"))),
            "total_uncovered_pieces": _to_pieces(total, unit),
            "demand_count": len(ordered),
            "origins": sorted({line.source for line in ordered}),
            "schedule": schedule,
        })

    result.sort(
        key=lambda item: (
            item["suggested_op_date"] or "9999-12-31",
            item["required_date"] or "9999-12-31",
            item["product_code"],
        )
    )
    return {
        "as_of": today.isoformat(),
        "branch": branch,
        "items": result,
        "count": len(result),
        "suppressed_product_count": len(suppressed),
        "total_uncovered_pieces": (
            sum(item["total_uncovered_pieces"] for item in result)
            if result and all(item["total_uncovered_pieces"] is not None for item in result)
            else None
        ),
    }
