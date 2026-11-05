"""Lista itens de NF de saída — filtros branch/cliente/loja + lote de produtos."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoice_line_items_repository import (
    CustomerOutboundInvoiceLineItemsRepository,
)

MAX_PRODUCT_CODES = 500
ALLOWED_BRANCHES = frozenset({"01", "02"})
# Necessidades MyWEG são em UN; sem fator confiável, outras UMs não entram no FIFO.
COMPARABLE_NEED_UNITS = frozenset({"UN", "UN."})


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

        # Dedup por identidade fiscal (filial+doc+série+item) — defesa se JOIN SB1 vazar.
        unique_items: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str, str, str]] = set()
        for item in items:
            key = (
                str(item.get("branch") or ""),
                str(item.get("invoice_number") or ""),
                str(item.get("invoice_series") or ""),
                str(item.get("item") or ""),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_items.append(item)

        totals: dict[str, dict[str, Any]] = {}
        for item in unique_items:
            if item.get("is_return"):
                continue
            code = item["product_code"]
            unit = self._effective_unit(item)
            try:
                qty = Decimal(str(item.get("quantity") or "0"))
            except (InvalidOperation, ValueError):
                qty = Decimal("0")
            bucket = totals.get(code)
            if bucket is None:
                totals[code] = {
                    "quantity": qty,
                    "unit": unit,
                    "units_seen": {unit} if unit else set(),
                    "comparable": unit in COMPARABLE_NEED_UNITS if unit else False,
                }
            else:
                bucket["quantity"] = bucket["quantity"] + qty
                if unit:
                    bucket["units_seen"].add(unit)
                if len(bucket["units_seen"]) > 1:
                    bucket["comparable"] = False
                    bucket["unit"] = "|".join(sorted(bucket["units_seen"]))
                elif unit and unit not in COMPARABLE_NEED_UNITS:
                    bucket["comparable"] = False

        totals_by_product: list[dict[str, Any]] = []
        for code, bucket in sorted(totals.items()):
            comparable = bool(bucket["comparable"])
            reason = None
            if not comparable:
                units = sorted(bucket["units_seen"]) or [bucket.get("unit") or ""]
                reason = (
                    "Unidade fiscal incompatível ou mista sem fator de conversão "
                    f"confiável para UN ({', '.join(u or '?' for u in units)})."
                )
            totals_by_product.append(
                {
                    "product_code": code,
                    "quantity": str(bucket["quantity"]),
                    "unit": bucket.get("unit") or None,
                    "comparable": comparable,
                    "incompatibility_reason": reason,
                }
            )

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
            "returned_item_count": len(unique_items),
            "items": unique_items,
            "totals_by_product": totals_by_product,
            "coverage": {
                "filters": {
                    "D2_FILIAL": branch_n,
                    "D2_CLIENTE": customer,
                    "D2_LOJA": store,
                },
                "cancellations": "soft_delete_SF2_SD2",
                "returns": "excluded" if exclude_returns else "included",
                "quantity_authority": "D2_QUANT_as_decimal_string",
                "unit_authority": "D2_UM_preferred_B1_UM_catalog_fallback",
                "sb1_join": "B1_FILIAL=D2_FILIAL to avoid duplicate catalog rows",
                "limitations": [
                    "Não prova reconhecimento do abatimento pela WEG.",
                    "Granularidade temporal é a data de emissão (sem horário de fechamento).",
                    "Unidades diferentes de UN não são convertidas automaticamente.",
                ],
            },
        }

    @staticmethod
    def _effective_unit(item: dict[str, Any]) -> str:
        invoice = str(item.get("invoice_unit") or "").strip().upper()
        if invoice:
            return invoice
        unit = str(item.get("unit") or "").strip().upper()
        if unit:
            return unit
        return str(item.get("catalog_unit") or "").strip().upper()
