"""Lista itens de NF de saída — filtros branch/cliente/loja + lote de produtos."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoice_line_items_repository import (
    CustomerOutboundInvoiceLineItemsRepository,
)

MAX_PRODUCT_CODES = 500
ALLOWED_BRANCHES = frozenset({"01", "02"})


class ListCustomerOutboundInvoiceLineItemsUseCase:
    def __init__(
        self, repository: CustomerOutboundInvoiceLineItemsRepository | None = None
    ) -> None:
        self._repository = repository or CustomerOutboundInvoiceLineItemsRepository()

    def execute(
        self,
        *,
        branch: str,
        customer_code: str,
        customer_store: str,
        issue_date_start: str,
        issue_date_end: str,
        product_codes: list[str],
        exclude_returns: bool = True,
    ) -> dict[str, Any]:
        branch_n = str(branch or "").strip()
        if branch_n not in ALLOWED_BRANCHES:
            raise ValueError("branch inválida. Use '01' ou '02'.")
        customer = str(customer_code or "").strip()
        store = str(customer_store or "").strip()
        if not customer or not store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        start = str(issue_date_start or "").strip()
        end = str(issue_date_end or "").strip()
        if not start or not end:
            raise ValueError("issue_date_start e issue_date_end são obrigatórios.")
        codes = [str(c).strip() for c in product_codes if str(c or "").strip()]
        if len(codes) > MAX_PRODUCT_CODES:
            raise ValueError(f"Limite de {MAX_PRODUCT_CODES} product_codes excedido.")

        items = self._repository.list_line_items(
            branch=branch_n,
            customer_code=customer,
            customer_store=store,
            issue_date_start=start,
            issue_date_end=end,
            product_codes=codes,
            exclude_returns=exclude_returns,
        )

        totals: dict[str, Decimal] = {}
        for item in items:
            if item.get("is_return"):
                continue
            code = item["product_code"]
            try:
                qty = Decimal(str(item.get("quantity") or "0"))
            except (InvalidOperation, ValueError):
                qty = Decimal("0")
            totals[code] = totals.get(code, Decimal("0")) + qty

        return {
            "branch": branch_n,
            "customer_code": customer,
            "customer_store": store,
            "issue_date_start": start[:10],
            "issue_date_end": end[:10],
            "exclude_returns": exclude_returns,
            "read_only": True,
            "side_effects": False,
            "requested_product_codes": codes,
            "returned_item_count": len(items),
            "items": items,
            "totals_by_product": [
                {"product_code": code, "quantity": str(qty)}
                for code, qty in sorted(totals.items())
            ],
            "coverage": {
                "filters": {
                    "D2_FILIAL": branch_n,
                    "D2_CLIENTE": customer,
                    "D2_LOJA": store,
                },
                "cancellations": "soft_delete_SF2_SD2",
                "returns": "excluded" if exclude_returns else "included",
                "quantity_authority": "D2_QUANT_as_decimal_string",
                "limitations": [
                    "Não prova reconhecimento do abatimento pela WEG.",
                    "Granularidade temporal é a data de emissão (sem horário de fechamento).",
                ],
            },
        }
