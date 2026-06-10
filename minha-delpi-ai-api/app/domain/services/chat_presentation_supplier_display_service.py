"""Rótulos de fornecedor (nome + loja) para tabelas e árvores de compra."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatPresentationSupplierDisplayService:
    @classmethod
    def supplier_name(cls, item: dict[str, Any]) -> str:
        return str(item.get("supplier_name") or "").strip()

    @classmethod
    def supplier_code(cls, item: dict[str, Any]) -> str:
        return str(item.get("supplier_code") or "").strip()

    @classmethod
    def supplier_store(cls, item: dict[str, Any]) -> str:
        return str(item.get("supplier_store") or "").strip()

    @classmethod
    def format_store_label(cls, store: str) -> str:
        token = str(store or "").strip()

        if not token:
            return ""

        template = ChatAssistantContentService.format(
            "presenter_content",
            "routePresentations",
            "purchaseHistoryShared",
            "supplierStoreLabel",
            store=token,
        )

        return str(template or "").strip()

    @classmethod
    def format_supplier_label(
        cls,
        *,
        supplier_code: str = "",
        supplier_name: str = "",
        supplier_store: str = "",
    ) -> str:
        code = str(supplier_code or "").strip()
        name = str(supplier_name or "").strip()
        store_label = cls.format_store_label(supplier_store)

        if name and code and store_label:
            return ChatAssistantContentService.format(
                "presenter_content",
                "routePresentations",
                "purchaseHistoryShared",
                "supplierLabelWithNameStore",
                name=name,
                code=code,
                store=store_label,
            )

        if name and code:
            return ChatAssistantContentService.format(
                "presenter_content",
                "routePresentations",
                "purchaseHistoryShared",
                "supplierLabelWithName",
                name=name,
                code=code,
            )

        if code and store_label:
            return ChatAssistantContentService.format(
                "presenter_content",
                "routePresentations",
                "purchaseHistoryShared",
                "supplierLabelCodeStore",
                code=code,
                store=store_label,
            )

        return code or name or "—"

    @classmethod
    def enrich_item(cls, item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict):
            return item

        enriched = dict(item)
        enriched["supplier_group"] = cls.format_supplier_label(
            supplier_code=cls.supplier_code(item),
            supplier_name=cls.supplier_name(item),
            supplier_store=cls.supplier_store(item),
        )
        return enriched

    @classmethod
    def enrich_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.enrich_item(item) for item in items if isinstance(item, dict)]
