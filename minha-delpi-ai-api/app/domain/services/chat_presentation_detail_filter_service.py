"""Filtra payload da API após nova consulta para detalhe de linha/nó."""

from __future__ import annotations

import re
from typing import Any


class ChatPresentationDetailFilterService:
    @classmethod
    def apply(cls, data: Any, detail_filter: dict[str, str] | None) -> Any:
        if not isinstance(data, dict) or not isinstance(detail_filter, dict) or not detail_filter:
            return data

        filtered = dict(data)
        items = filtered.get("items")
        product_prefix = re.sub(
            r"\D",
            "",
            str(detail_filter.get("product_code_prefix") or ""),
        )

        if isinstance(items, list):
            narrowed = cls._filter_items(items, detail_filter)

            if narrowed or product_prefix:
                filtered["items"] = narrowed
                filtered["query_context"] = {
                    "product_code_prefix": product_prefix,
                }
                return filtered

        page_items = None

        if isinstance(filtered.get("page"), dict):
            page_items = filtered["page"].get("items")

        if isinstance(page_items, list):
            narrowed = cls._filter_items(page_items, detail_filter)

            if narrowed:
                page = dict(filtered["page"])
                page["items"] = narrowed
                filtered["page"] = page
                return filtered

        budget_history = filtered.get("budget_history")

        if isinstance(budget_history, dict) and isinstance(budget_history.get("items"), list):
            narrowed = cls._filter_items(budget_history["items"], detail_filter)

            if narrowed:
                section = dict(budget_history)
                section["items"] = narrowed
                filtered["budget_history"] = section

        price_history = filtered.get("price_history")

        if isinstance(price_history, dict) and isinstance(price_history.get("items"), list):
            narrowed = cls._filter_items(price_history["items"], detail_filter)

            if narrowed:
                section = dict(price_history)
                section["items"] = narrowed
                filtered["price_history"] = section

        resultsets = filtered.get("resultsets")

        if isinstance(resultsets, list) and product_prefix:
            changed = False
            narrowed_resultsets: list[Any] = []

            for resultset in resultsets:
                if not isinstance(resultset, dict):
                    narrowed_resultsets.append(resultset)
                    continue

                rows = resultset.get("rows")

                if not isinstance(rows, list):
                    narrowed_resultsets.append(resultset)
                    continue

                narrowed_rows = cls._filter_items(rows, detail_filter)
                next_resultset = dict(resultset)
                next_resultset["rows"] = narrowed_rows
                narrowed_resultsets.append(next_resultset)
                changed = True

            if changed:
                filtered["resultsets"] = narrowed_resultsets
                filtered["query_context"] = {
                    "product_code_prefix": product_prefix,
                }

        return filtered

    @classmethod
    def _filter_items(
        cls,
        items: list[Any],
        detail_filter: dict[str, str],
    ) -> list[dict[str, Any]]:
        supplier_code = str(detail_filter.get("supplier_code") or "").strip()
        supplier_store = str(detail_filter.get("supplier_store") or "").strip()
        document_number = str(detail_filter.get("document_number") or "").strip()
        source = str(detail_filter.get("source") or "").strip()
        product_code_prefix = re.sub(
            r"\D",
            "",
            str(detail_filter.get("product_code_prefix") or ""),
        )

        narrowed: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            if product_code_prefix and not cls._item_matches_product_code_prefix(
                item,
                product_code_prefix,
            ):
                continue

            if document_number and str(item.get("document_number") or "").strip() != document_number:
                continue

            if source and str(item.get("source") or "").strip().upper() != source.upper():
                continue

            if supplier_code and str(item.get("supplier_code") or "").strip() != supplier_code:
                continue

            if supplier_store:
                store = str(item.get("supplier_store") or "").strip().zfill(2)

                if store != supplier_store.zfill(2):
                    continue

            narrowed.append(item)

        return narrowed

    @classmethod
    def _item_matches_product_code_prefix(
        cls,
        item: dict[str, Any],
        product_code_prefix: str,
    ) -> bool:
        for key in (
            "product_code",
            "item_code",
            "material_code",
            "component_code",
            "code",
            "cod_produto",
            "COD_PRODUTO",
            "C2_PRODUTO",
        ):
            token = re.sub(r"\D", "", str(item.get(key) or ""))

            if token.startswith(product_code_prefix):
                return True

        return False
