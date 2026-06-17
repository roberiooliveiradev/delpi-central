"""Insights de precificação — canônico para dataAnswer (desacoplado do markdown do presenter)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)

_ROUTE = "salePricing"


class ChatProductPricingInsightService:
    @classmethod
    def build_commentary(cls, root: dict[str, Any]) -> dict[str, Any] | None:
        prices = root.get("prices")

        if not isinstance(prices, list):
            return None

        items = [item for item in prices if isinstance(item, dict)]

        if not items:
            return None

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(product.get("code") or product.get("product_code") or "").strip()
        description = str(product.get("description") or product.get("product_description") or "").strip()
        unit = str(product.get("unit") or "").strip()
        highlights: list[str] = []
        attention: list[str] = []

        ordered = sorted(items, key=lambda item: float(item.get("sale_price") or 0))
        min_item = ordered[0]
        max_item = ordered[-1]
        min_price = float(min_item.get("sale_price") or 0)
        max_price = float(max_item.get("sale_price") or 0)

        if description or unit:
            highlights.append(
                cls._route(
                    "panoramaProductLine",
                    code=code or "—",
                    description=description or "—",
                    unit=unit or "—",
                    count=str(len(items)),
                )
            )

        highlights.append(
            cls._route(
                "panoramaMinLine",
                price=cls._format_price(min_price),
                tableCode=str(min_item.get("table_code") or "—"),
                table=str(min_item.get("table_description") or min_item.get("table_code") or "—"),
            )
        )

        if len(items) > 1:
            highlights.append(
                cls._route(
                    "panoramaMaxLine",
                    price=cls._format_price(max_price),
                    tableCode=str(max_item.get("table_code") or "—"),
                    table=str(max_item.get("table_description") or max_item.get("table_code") or "—"),
                )
            )

            delta = max_price - min_price
            percent = (delta / min_price * 100) if min_price else 0.0
            highlights.append(
                cls._route(
                    "panoramaRangeLine",
                    delta=cls._format_price(delta),
                    percent=cls._format_percent(percent),
                )
            )

        commentary = {
            "profileKey": "sale_pricing",
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
        }

        return ChatHumanizedDataResponseService.normalize(commentary, profile_key="sale_pricing")

    @classmethod
    def _route(cls, key: str, **values: str) -> str:
        if values:
            return ChatAssistantContentService.format(
                "presenter_content",
                "routePresentations",
                _ROUTE,
                key,
                **values,
            )

        return ChatAssistantContentService.get(
            "presenter_content",
            "routePresentations",
            _ROUTE,
            key,
            default="",
        )

    @classmethod
    def _format_price(cls, value: float) -> str:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @classmethod
    def _format_percent(cls, value: float) -> str:
        return f"{value:.1f}".replace(".", ",")
