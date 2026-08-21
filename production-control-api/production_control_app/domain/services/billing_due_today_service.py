"""Checklist de faturamento do dia — pedidos com entrega até hoje.

A gestão à vista do PCP precisa ver, por cliente, o que deveria sair (faturar)
até hoje e o progresso:

- **amarelo** — saldo ainda aberto, mas coberta por estoque (pode faturar);
- **verde** — linha encerrada no TOTVS com ``C6_DATFAT`` = hoje (faturada de verdade);
- sem check — ainda aberta e sem cobertura de estoque.

A alocação de estoque reusa o FIFO de ``DemandCoverageService`` (sem OPs: o
sinal do card é só «há físico para faturar»).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from production_control_app.domain.services.demand_coverage_service import (
    DemandCoverageService,
    DemandLine,
)
from production_control_app.domain.services.demand_entity_scope import is_customer_sales_entity

CHECK_PENDING = "pending"
CHECK_STOCK = "stock"
CHECK_INVOICED = "invoiced"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_qty(value: Any) -> float:
    try:
        return round(float(value), 3)
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


def _line_key(branch: str, sales_order: str, line_item: str) -> str:
    return f"{branch}|{sales_order}|{line_item}"


class BillingDueTodayService:
    """Monta o card «a faturar até hoje» a partir de abertos + recently-closed."""

    def __init__(self, *, today: date | None = None) -> None:
        self._today = today

    def _reference_date(self) -> date:
        return self._today or date.today()

    def build(
        self,
        *,
        open_sales_orders: Iterable[Any],
        recently_closed_orders: Iterable[Any],
        branch: str,
    ) -> dict[str, Any]:
        today = self._reference_date()
        # Estoque FIFO basta para o check amarelo; OPs não mudam «pode faturar».
        open_lines = DemandCoverageService(today=today).build(
            open_sales_orders=open_sales_orders,
            open_production_orders=[],
            branch=branch,
        )
        due_open = [
            line
            for line in open_lines
            if line.due_date is not None and line.due_date <= today
        ]

        invoiced_by_key = self._invoiced_today(
            recently_closed_orders,
            branch=branch,
            today=today,
        )

        # Linha ainda aberta não aparece como verde — o encerramento TOTVS manda.
        rows: list[dict[str, Any]] = []
        open_keys: set[str] = set()
        for line in due_open:
            open_keys.add(line.key)
            rows.append(self._open_row(line, today=today))

        for key, item in invoiced_by_key.items():
            if key in open_keys:
                continue
            rows.append(item)

        customers = self._group_customers(rows)
        pending = sum(1 for row in rows if row["check"] == CHECK_PENDING)
        stock = sum(1 for row in rows if row["check"] == CHECK_STOCK)
        invoiced = sum(1 for row in rows if row["check"] == CHECK_INVOICED)

        return {
            "as_of": today.isoformat(),
            "line_count": len(rows),
            "pending_count": pending,
            "stock_count": stock,
            "invoiced_count": invoiced,
            "customers": customers,
        }

    def _open_row(self, line: DemandLine, *, today: date) -> dict[str, Any]:
        covered_by_stock = line.allocated_stock >= line.open_quantity - 1e-9
        return {
            "id": line.key,
            "branch": line.branch,
            "sales_order": line.sales_order,
            "line_item": line.line_item,
            "customer_code": line.customer_code,
            "customer_store": line.customer_store,
            "customer_name": line.customer_name,
            "customer_order": line.customer_order,
            "order_type": line.order_type,
            "product_code": line.product_code,
            "ordered_quantity": round(line.ordered_quantity, 3),
            "delivered_quantity": round(line.delivered_quantity, 3),
            "open_quantity": round(line.open_quantity, 3),
            "product_stock": round(line.product_stock, 3),
            "allocated_stock": round(line.allocated_stock, 3),
            "uncovered_quantity": round(line.uncovered_quantity, 3),
            "due_date": line.due_date.isoformat() if line.due_date else None,
            "dispatch_date": line.dispatch_date.isoformat() if line.dispatch_date else None,
            "invoice_date": None,
            "check": CHECK_STOCK if covered_by_stock else CHECK_PENDING,
            "days_late": line.days_late(today),
        }

    def _invoiced_today(
        self,
        items: Iterable[Any],
        *,
        branch: str,
        today: date,
    ) -> dict[str, dict[str, Any]]:
        today_s = today.isoformat()
        result: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            item_branch = _text(item.get("filial"))
            if item_branch != branch:
                continue
            if not is_customer_sales_entity(item.get("tipo_entidade")):
                continue
            invoice_date = _iso_date(item.get("data_faturamento"))
            if invoice_date is None or invoice_date.isoformat() != today_s:
                continue
            due_date = _iso_date(item.get("data_entrega"))
            # Só entra no card se a entrega prometida era até hoje (ou sem data).
            if due_date is not None and due_date > today:
                continue
            sales_order = _text(item.get("pedido"))
            line_item = _text(item.get("linha"))
            key = _line_key(item_branch, sales_order, line_item)
            dispatch_date = _iso_date(item.get("data_despacho"))
            result[key] = {
                "id": key,
                "branch": item_branch,
                "sales_order": sales_order,
                "line_item": line_item,
                "customer_code": _text(item.get("codigo_cadastro"))
                or _text(item.get("codigo_cliente")),
                "customer_store": _text(item.get("loja_cadastro")),
                "customer_name": _text(item.get("nome_cliente")),
                "customer_order": _text(item.get("pedido_cliente")),
                "order_type": _text(item.get("tipo_pedido")),
                "product_code": _text(item.get("produto")),
                "ordered_quantity": _as_qty(item.get("quantidade")),
                "delivered_quantity": _as_qty(item.get("entregue")),
                "open_quantity": 0.0,
                "product_stock": 0.0,
                "allocated_stock": 0.0,
                "uncovered_quantity": 0.0,
                "due_date": due_date.isoformat() if due_date else None,
                "dispatch_date": dispatch_date.isoformat() if dispatch_date else None,
                "invoice_date": today_s,
                "check": CHECK_INVOICED,
                "days_late": 0
                if due_date is None or due_date >= today
                else (today - due_date).days,
            }
        return result

    def _group_customers(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        order = {CHECK_PENDING: 0, CHECK_STOCK: 1, CHECK_INVOICED: 2}
        groups: dict[str, dict[str, Any]] = {}
        for row in rows:
            customer_key = (
                f"{row.get('customer_code')}|{row.get('customer_store')}|"
                f"{row.get('customer_name')}"
            )
            group = groups.get(customer_key)
            if group is None:
                group = {
                    "customer_code": row.get("customer_code") or "",
                    "customer_store": row.get("customer_store") or "",
                    "customer_name": row.get("customer_name") or "—",
                    "lines": [],
                }
                groups[customer_key] = group
            group["lines"].append(row)

        customers = list(groups.values())
        for group in customers:
            group["lines"].sort(
                key=lambda line: (
                    order.get(str(line.get("check")), 9),
                    str(line.get("due_date") or ""),
                    str(line.get("product_code") or ""),
                    str(line.get("sales_order") or ""),
                )
            )
            group["line_count"] = len(group["lines"])
            group["pending_count"] = sum(
                1 for line in group["lines"] if line.get("check") == CHECK_PENDING
            )
            group["stock_count"] = sum(
                1 for line in group["lines"] if line.get("check") == CHECK_STOCK
            )
            group["invoiced_count"] = sum(
                1 for line in group["lines"] if line.get("check") == CHECK_INVOICED
            )

        customers.sort(
            key=lambda group: (
                -int(group.get("pending_count") or 0),
                -int(group.get("stock_count") or 0),
                str(group.get("customer_name") or "").casefold(),
            )
        )
        return customers
