"""Cobertura da demanda — quem atende cada saldo de pedido.

O PCP não pergunta «posso faturar», e sim «o que precisa sair da fábrica». Por
isso a cobertura é montada em duas camadas, sempre por ``(filial, produto)`` e
sempre na ordem de entrega (quem vence antes consome primeiro):

1. **Estoque** — o saldo disponível do produto é distribuído entre as linhas.
2. **OPs abertas** — o que o estoque não cobriu é distribuído entre as ordens de
   produção em aberto, da que termina antes para a que termina depois.

O que sobra sem estoque nem OP é demanda descoberta: é o sinal que o PCP quer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable

from production_control_app.domain.services.demand_entity_scope import is_customer_sales_entity

STATUS_LATE = "late"
STATUS_AT_RISK = "at_risk"
STATUS_COVERED_BY_ORDER = "covered_by_order"
STATUS_COVERED_BY_STOCK = "covered_by_stock"

# Sem data de entrega a linha não pode ser classificada como atrasada; vai para
# o fim da fila de alocação, como na carga máquina.
_FAR_FUTURE = date(9999, 12, 31)
# Quantidades TOTVS em float (0,75 − 0,6 − 0,15) deixam residual ~1e-16; sem
# epsilon a próxima OP entra com qty 0,0 e envenena coverage_date / status.
_QTY_EPS = 1e-6


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _iso_date(value: Any) -> date | None:
    text = _text(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


@dataclass(slots=True)
class _OpenOrderSupply:
    """OP aberta disponível para cobrir demanda de um produto."""

    order_number: str
    remaining: float
    expected_date: date | None


@dataclass(slots=True)
class DemandLine:
    """Linha de pedido com saldo, já enriquecida com a cobertura."""

    branch: str
    sales_order: str
    line_item: str
    customer_name: str
    customer_code: str
    customer_store: str
    customer_order: str
    order_type: str
    product_code: str
    ordered_quantity: float
    delivered_quantity: float
    open_quantity: float
    due_date: date | None
    dispatch_date: date | None
    product_stock: float
    allocated_stock: float = 0.0
    covering_orders: list[dict[str, Any]] = field(default_factory=list)
    uncovered_quantity: float = 0.0
    coverage_date: date | None = None
    status: str = STATUS_AT_RISK

    @property
    def key(self) -> str:
        return f"{self.branch}|{self.sales_order}|{self.line_item}"

    def days_late(self, today: date) -> int:
        if self.due_date is None or self.due_date >= today:
            return 0
        return (today - self.due_date).days

    def to_dict(self, today: date) -> dict[str, Any]:
        """Projeção para o BFF. Sem preço nem valor: o PCP olha quantidade."""
        return {
            "id": self.key,
            "branch": self.branch,
            "sales_order": self.sales_order,
            "line_item": self.line_item,
            "customer_name": self.customer_name,
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_order": self.customer_order,
            "order_type": self.order_type,
            "product_code": self.product_code,
            "ordered_quantity": round(self.ordered_quantity, 3),
            "delivered_quantity": round(self.delivered_quantity, 3),
            "open_quantity": round(self.open_quantity, 3),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "dispatch_date": self.dispatch_date.isoformat() if self.dispatch_date else None,
            "product_stock": round(self.product_stock, 3),
            "allocated_stock": round(self.allocated_stock, 3),
            "covered_by_orders": round(
                sum(_number(item.get("quantity")) for item in self.covering_orders), 3
            ),
            "uncovered_quantity": round(self.uncovered_quantity, 3),
            "covering_orders": self.covering_orders,
            "coverage_date": self.coverage_date.isoformat() if self.coverage_date else None,
            "status": self.status,
            "days_late": self.days_late(today),
        }


class DemandCoverageService:
    """Constrói as linhas de demanda com a cobertura de estoque e de OP."""

    def __init__(self, *, today: date | None = None) -> None:
        self._today = today

    def _reference_date(self) -> date:
        return self._today or date.today()

    # ------------------------------------------------------------- parsing

    def _build_lines(self, items: Iterable[Any]) -> list[DemandLine]:
        lines: list[DemandLine] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            open_quantity = _number(item.get("saldo"))
            if open_quantity <= 0:
                continue
            if not is_customer_sales_entity(item.get("tipo_entidade")):
                continue
            lines.append(
                DemandLine(
                    branch=_text(item.get("filial")),
                    sales_order=_text(item.get("pedido")),
                    line_item=_text(item.get("linha")),
                    customer_name=_text(item.get("nome_cliente")),
                    customer_code=_text(item.get("codigo_cadastro"))
                    or _text(item.get("codigo_cliente")),
                    customer_store=_text(item.get("loja_cadastro")),
                    customer_order=_text(item.get("pedido_cliente")),
                    order_type=_text(item.get("tipo_pedido")),
                    product_code=_text(item.get("produto")),
                    ordered_quantity=_number(item.get("quantidade")),
                    delivered_quantity=_number(item.get("entregue")),
                    open_quantity=open_quantity,
                    due_date=_iso_date(item.get("data_entrega")),
                    dispatch_date=_iso_date(item.get("data_despacho")),
                    product_stock=_number(item.get("no_estoque")),
                )
            )
        return lines

    def _build_supplies(self, items: Iterable[Any]) -> dict[tuple[str, str], list[_OpenOrderSupply]]:
        """OPs abertas agrupadas por ``(filial, produto)``, da mais próxima de terminar."""
        supplies: dict[tuple[str, str], list[_OpenOrderSupply]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            remaining = _number(item.get("saldo_op"))
            if remaining <= 0:
                continue
            key = (_text(item.get("filial")), _text(item.get("produto")))
            supplies.setdefault(key, []).append(
                _OpenOrderSupply(
                    order_number=_text(item.get("numero_op")),
                    remaining=remaining,
                    expected_date=_iso_date(item.get("data_fim_prevista_op")),
                )
            )
        for entries in supplies.values():
            entries.sort(key=lambda entry: (entry.expected_date or _FAR_FUTURE, entry.order_number))
        return supplies

    # ---------------------------------------------------------- allocation

    def _allocate(
        self,
        lines: list[DemandLine],
        supplies: dict[tuple[str, str], list[_OpenOrderSupply]],
    ) -> None:
        by_product: dict[tuple[str, str], list[DemandLine]] = {}
        for line in lines:
            by_product.setdefault((line.branch, line.product_code), []).append(line)

        for key, group in by_product.items():
            group.sort(key=lambda item: (item.due_date or _FAR_FUTURE, item.sales_order, item.line_item))
            # O estoque vem repetido em cada linha da view: uma leitura basta.
            available_stock = max(group[0].product_stock, 0.0)
            queue = [
                _OpenOrderSupply(entry.order_number, entry.remaining, entry.expected_date)
                for entry in supplies.get(key, ())
            ]

            for line in group:
                pending = line.open_quantity
                taken = min(pending, available_stock)
                if taken <= _QTY_EPS:
                    taken = 0.0
                line.allocated_stock = round(taken, 3)
                available_stock = max(available_stock - taken, 0.0)
                pending = max(pending - taken, 0.0)

                for supply in queue:
                    if pending <= _QTY_EPS:
                        break
                    if supply.remaining <= _QTY_EPS:
                        continue
                    used = min(pending, supply.remaining)
                    qty = round(used, 3)
                    if qty <= 0:
                        # Residual de float — não registra OP fantasma.
                        pending = 0.0
                        break
                    supply.remaining -= used
                    pending = max(pending - used, 0.0)
                    line.covering_orders.append(
                        {
                            "production_order": supply.order_number,
                            "quantity": qty,
                            "expected_date": (
                                supply.expected_date.isoformat() if supply.expected_date else None
                            ),
                        }
                    )
                    if supply.expected_date and (
                        line.coverage_date is None or supply.expected_date > line.coverage_date
                    ):
                        line.coverage_date = supply.expected_date

                if pending <= _QTY_EPS:
                    line.uncovered_quantity = 0.0
                else:
                    line.uncovered_quantity = round(pending, 3)

    # ------------------------------------------------------- classification

    def _classify(self, line: DemandLine, today: date) -> str:
        if line.due_date is not None and line.due_date < today:
            return STATUS_LATE
        if line.uncovered_quantity > _QTY_EPS:
            return STATUS_AT_RISK
        if line.covering_orders:
            # OP prevista depois da entrega não resolve o compromisso.
            if (
                line.due_date is not None
                and line.coverage_date is not None
                and line.coverage_date > line.due_date
            ):
                return STATUS_AT_RISK
            return STATUS_COVERED_BY_ORDER
        return STATUS_COVERED_BY_STOCK

    # ---------------------------------------------------------------- public

    def build(
        self,
        *,
        open_sales_orders: Iterable[Any],
        open_production_orders: Iterable[Any],
        branch: str | None = None,
    ) -> list[DemandLine]:
        lines = self._build_lines(open_sales_orders)
        if branch:
            lines = [line for line in lines if line.branch == branch]
        self._allocate(lines, self._build_supplies(open_production_orders))
        today = self._reference_date()
        for line in lines:
            line.status = self._classify(line, today)
        return lines
