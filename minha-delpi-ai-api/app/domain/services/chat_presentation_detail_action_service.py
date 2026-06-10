"""Ações de detalhe em apresentações ricas — consulta API, não montagem do histórico."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@dataclass(frozen=True)
class PresentationDetailPlan:
    kind: str
    product_code: str
    path_fragment: str
    query: str
    previous_path: str | None = None
    previous_parameters: dict[str, Any] | None = None
    detail_filter: dict[str, str] | None = None


class ChatPresentationDetailActionService:
    _SUPPLIER_DETAIL_RE = re.compile(
        r"detalhe\s+fornecedor\s+(\d{3,})\s+loja\s+(\d{1,3})\s+do\s+produto\s+(\d{4,})",
        re.IGNORECASE,
    )
    _PURCHASE_RECORD_DETAIL_RE = re.compile(
        r"detalhe\s+documento\s+(\S+)\s+origem\s+(\S+)\s+do\s+produto\s+(\d{4,})",
        re.IGNORECASE,
    )

    @classmethod
    def build_supplier_detail_query(
        cls,
        *,
        product_code: str,
        supplier_code: str,
        supplier_store: str,
    ) -> str:
        return ChatAssistantContentService.format(
            "interactivity",
            "presentationDetailQueries",
            "supplier",
            productCode=str(product_code or "").strip(),
            supplierCode=str(supplier_code or "").strip(),
            supplierStore=str(supplier_store or "").strip(),
        )

    @classmethod
    def build_purchase_record_detail_query(
        cls,
        *,
        product_code: str,
        document_number: str,
        source: str,
    ) -> str:
        return ChatAssistantContentService.format(
            "interactivity",
            "presentationDetailQueries",
            "purchaseRecord",
            productCode=str(product_code or "").strip(),
            documentNumber=str(document_number or "").strip(),
            source=str(source or "").strip(),
        )

    @classmethod
    def supplier_detail_meta(
        cls,
        *,
        product_code: str,
        supplier_code: str,
        supplier_store: str,
    ) -> dict[str, str]:
        return {
            "detailKind": "supplier",
            "productCode": str(product_code or "").strip(),
            "supplierCode": str(supplier_code or "").strip(),
            "supplierStore": str(supplier_store or "").strip(),
            "detailQuery": cls.build_supplier_detail_query(
                product_code=product_code,
                supplier_code=supplier_code,
                supplier_store=supplier_store,
            ),
        }

    @classmethod
    def purchase_record_detail_meta(
        cls,
        *,
        product_code: str,
        document_number: str,
        source: str,
        supplier_code: str = "",
        supplier_store: str = "",
    ) -> dict[str, str]:
        meta = {
            "detailKind": "purchase_record",
            "productCode": str(product_code or "").strip(),
            "documentNumber": str(document_number or "").strip(),
            "source": str(source or "").strip(),
            "detailQuery": cls.build_purchase_record_detail_query(
                product_code=product_code,
                document_number=document_number,
                source=source,
            ),
        }

        if supplier_code:
            meta["supplierCode"] = supplier_code

        if supplier_store:
            meta["supplierStore"] = supplier_store

        return meta

    @classmethod
    def detect_plan(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> PresentationDetailPlan | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        supplier_match = cls._SUPPLIER_DETAIL_RE.search(normalized)

        if supplier_match:
            product_code = supplier_match.group(3).strip()
            previous = cls._resolve_purchase_context(previous_messages)

            return PresentationDetailPlan(
                kind="supplier_detail",
                product_code=product_code,
                path_fragment="/suppliers",
                query=str(message or "").strip(),
                previous_path=previous.get("path") if previous else None,
                previous_parameters=previous.get("parameters") if previous else None,
                detail_filter={
                    "supplier_code": supplier_match.group(1).strip(),
                    "supplier_store": supplier_match.group(2).strip().zfill(2),
                },
            )

        record_match = cls._PURCHASE_RECORD_DETAIL_RE.search(normalized)

        if record_match:
            product_code = record_match.group(3).strip()
            previous = cls._resolve_purchase_context(previous_messages)
            path_fragment = cls._purchase_history_path(previous)

            return PresentationDetailPlan(
                kind="purchase_record_detail",
                product_code=product_code,
                path_fragment=path_fragment,
                query=str(message or "").strip(),
                previous_path=previous.get("path") if previous else None,
                previous_parameters=previous.get("parameters") if previous else None,
                detail_filter={
                    "document_number": record_match.group(1).strip(),
                    "source": record_match.group(2).strip(),
                },
            )

        return None

    @classmethod
    def _purchase_history_path(cls, previous: dict[str, Any] | None) -> str:
        path = str((previous or {}).get("path") or "").lower()

        if "purchase-budget-history" in path:
            return "/purchase-budget-history"

        if "purchase-price-history" in path:
            return "/purchase-price-history"

        if "raw-material-price-intelligence" in path:
            return "/raw-material-price-intelligence"

        return "/purchase-budget-history"

    @classmethod
    def _resolve_purchase_context(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        for message in reversed(previous_messages or []):
            if not isinstance(message, dict):
                continue

            if str(message.get("role") or "").strip().lower() != "assistant":
                continue

            metadata = message.get("metadata")

            if not isinstance(metadata, dict):
                continue

            for call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(call, dict):
                    continue

                if str(call.get("name") or "") != "execute_external_action":
                    continue

                call_meta = call.get("metadata")

                if not isinstance(call_meta, dict) or not call_meta.get("ok"):
                    continue

                path = str(call_meta.get("path") or "").lower()

                if not any(
                    token in path
                    for token in (
                        "purchase-budget-history",
                        "purchase-price-history",
                        "raw-material-price-intelligence",
                    )
                ):
                    continue

                arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
                parameters = arguments.get("parameters") if isinstance(arguments.get("parameters"), dict) else {}

                return {
                    "path": str(call_meta.get("path") or ""),
                    "parameters": dict(parameters),
                }

        return None
