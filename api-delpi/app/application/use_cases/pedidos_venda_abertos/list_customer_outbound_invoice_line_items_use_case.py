"""Lista itens de NF de saída — filtros branch/cliente/loja + lote de produtos."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.domain.services.pedidos_venda_abertos.fiscal_quantity_to_un import (
    NORMALIZED_UNIT,
    convert_fiscal_quantity_to_un,
    decimal_to_plain_str,
)
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
            unique_items.append(self._enrich_item(item))

        totals: dict[str, dict[str, Any]] = {}
        for item in unique_items:
            if item.get("is_return"):
                continue
            code = item["product_code"]
            bucket = totals.get(code)
            if bucket is None:
                bucket = {
                    "original_quantity_by_unit": {},
                    "quantity_un": Decimal("0"),
                    "comparable_quantity_un": Decimal("0"),
                    "units_seen": set(),
                    "comparable_units": set(),
                    "incomparable_count": 0,
                    "comparable_item_count": 0,
                    "reasons": [],
                }
                totals[code] = bucket

            original_unit = str(item.get("unit") or "").strip().upper() or "?"
            bucket["units_seen"].add(original_unit)
            original_qty = item.get("quantity")
            try:
                original_dec = Decimal(str(original_qty)) if original_qty not in (None, "") else None
            except Exception:
                original_dec = None
            if original_dec is not None:
                by_unit = bucket["original_quantity_by_unit"]
                by_unit[original_unit] = by_unit.get(original_unit, Decimal("0")) + original_dec

            if item.get("comparable") and item.get("quantity_un") is not None:
                qty_un = Decimal(str(item["quantity_un"]))
                bucket["quantity_un"] += qty_un
                bucket["comparable_quantity_un"] += qty_un
                bucket["comparable_item_count"] += 1
                bucket["comparable_units"].add(original_unit)
            else:
                bucket["incomparable_count"] += 1
                reason = str(item.get("incompatibility_reason") or "").strip()
                if reason and reason not in bucket["reasons"]:
                    bucket["reasons"].append(reason)

        totals_by_product: list[dict[str, Any]] = []
        for code, bucket in sorted(totals.items()):
            units = sorted(bucket["units_seen"])
            original_by_unit = bucket["original_quantity_by_unit"]
            # quantity/unit brutos: só quando uma única unidade original (sem misturar MI+UN).
            if len(original_by_unit) == 1:
                only_unit = next(iter(original_by_unit))
                raw_quantity = decimal_to_plain_str(original_by_unit[only_unit])
                raw_unit = only_unit if only_unit != "?" else None
            else:
                raw_quantity = None
                raw_unit = None

            has_comparable = bucket["comparable_item_count"] > 0
            has_incomparable = bucket["incomparable_count"] > 0
            if has_comparable and not has_incomparable:
                comparable = True
                reason = None
            elif has_comparable and has_incomparable:
                comparable = True  # cobertura parcial — total_un só dos itens conversíveis
                reason = (
                    "Cobertura parcial: alguns itens do produto não foram normalizados "
                    "para UN; quantity_un soma apenas itens comparáveis. "
                    + ("; ".join(bucket["reasons"]) if bucket["reasons"] else "")
                ).strip()
            else:
                comparable = False
                reason = (
                    "; ".join(bucket["reasons"])
                    if bucket["reasons"]
                    else (
                        "Unidade fiscal incompatível ou mista sem fator de conversão "
                        f"confiável para UN ({', '.join(units)})."
                    )
                )

            factors = sorted(
                {
                    str(item.get("conversion_factor"))
                    for item in unique_items
                    if item.get("product_code") == code
                    and item.get("comparable")
                    and item.get("conversion_factor") is not None
                }
            )
            conversion_factor = factors[0] if len(factors) == 1 else (
                None if not factors else "|".join(factors)
            )

            totals_by_product.append(
                {
                    "product_code": code,
                    "quantity": raw_quantity,
                    "unit": raw_unit,
                    "original_units": units,
                    "quantity_un": (
                        decimal_to_plain_str(bucket["comparable_quantity_un"])
                        if has_comparable
                        else None
                    ),
                    "normalized_unit": NORMALIZED_UNIT if has_comparable else None,
                    "conversion_factor": conversion_factor,
                    "comparable": comparable,
                    "incompatibility_reason": reason,
                    "comparable_item_count": bucket["comparable_item_count"],
                    "incomparable_item_count": bucket["incomparable_count"],
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
                "unit_normalization": "UN_and_MI_to_UN_factor_1000_per_item_before_aggregate",
                "sb1_join": "B1_FILIAL=D2_FILIAL to avoid duplicate catalog rows",
                "limitations": [
                    "Não prova reconhecimento do abatimento pela WEG.",
                    "Granularidade temporal é a data de emissão (sem horário de fechamento).",
                    "Somente UN/UN./MI têm fator validado para necessidades em UN; outras UMs ficam não comparáveis.",
                    "quantity/unit permanecem brutos; quantity_un é a autoridade para FIFO.",
                ],
            },
        }

    def _enrich_item(self, item: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(item)
        unit = self._effective_unit(item)
        # Preserva unit efetiva (D2_UM) sem reescrever significado de quantity.
        enriched["unit"] = unit
        conversion = convert_fiscal_quantity_to_un(
            quantity=item.get("quantity"),
            unit=unit,
        )
        enriched["quantity_un"] = (
            decimal_to_plain_str(conversion.quantity_un)
            if conversion.quantity_un is not None
            else None
        )
        enriched["normalized_unit"] = conversion.normalized_unit
        enriched["conversion_factor"] = (
            decimal_to_plain_str(conversion.conversion_factor)
            if conversion.conversion_factor is not None
            else None
        )
        enriched["comparable"] = conversion.comparable
        enriched["incompatibility_reason"] = conversion.incompatibility_reason
        return enriched

    @staticmethod
    def _effective_unit(item: dict[str, Any]) -> str:
        invoice = str(item.get("invoice_unit") or "").strip().upper()
        if invoice:
            return invoice
        unit = str(item.get("unit") or "").strip().upper()
        if unit:
            return unit
        return str(item.get("catalog_unit") or "").strip().upper()
