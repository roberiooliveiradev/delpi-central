"""Filtra payload da API após nova consulta para detalhe de linha/nó."""

from __future__ import annotations

from typing import Any


class ChatPresentationDetailFilterService:
    @classmethod
    def apply(cls, data: Any, detail_filter: dict[str, str] | None) -> Any:
        if not isinstance(data, dict) or not isinstance(detail_filter, dict) or not detail_filter:
            return data

        filtered = dict(data)
        items = filtered.get("items")

        if isinstance(items, list):
            narrowed = cls._filter_items(items, detail_filter)

            if narrowed:
                filtered["items"] = narrowed
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

        narrowed: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
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
