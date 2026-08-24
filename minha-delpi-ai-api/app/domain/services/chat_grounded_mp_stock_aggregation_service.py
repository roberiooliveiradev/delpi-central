"""Agregação de estoque MP em fan-out grounded — commentary útil sem dump linha a linha."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService


class ChatGroundedMpStockAggregationService:
    @classmethod
    def should_aggregate(cls, message: str, tool_calls: list[Any] | None) -> bool:
        if not ChatTurnGroundingService.resolve_referent_component_type(message):
            return False

        stock_calls = cls._successful_stock_tool_calls(tool_calls)

        return len(stock_calls) >= 2

    @classmethod
    def build_merged_commentary(
        cls,
        message: str,
        tool_calls: list[Any] | None,
    ) -> dict[str, Any] | None:
        if not cls.should_aggregate(message, tool_calls):
            return None

        items = cls._merge_stock_items(tool_calls)

        if not items:
            return None

        root = {"items": items, "total": len(items), "aggregatedMpFanOut": True}

        return ChatOperationalDataCommentaryService._build_stock_commentary(root)

    @classmethod
    def commentary_lead_lines(cls, commentary: dict[str, Any] | None) -> list[str]:
        if not isinstance(commentary, dict):
            return []

        lines: list[str] = []

        for key in ("highlights", "attention", "summaryLines"):
            block = commentary.get(key)

            if not isinstance(block, list):
                continue

            for line in block:
                token = str(line or "").strip()

                if token and token not in lines:
                    lines.append(token)

        return lines[:8]

    @classmethod
    def _successful_stock_tool_calls(cls, tool_calls: list[Any] | None) -> list[dict[str, Any]]:
        matched: list[dict[str, Any]] = []

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "").strip().lower()

            if "/stock" not in path:
                continue

            matched.append(tool_call)

        return matched

    @classmethod
    def _merge_stock_items(cls, tool_calls: list[Any] | None) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for tool_call in cls._successful_stock_tool_calls(tool_calls):
            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            data = metadata.get("data")

            if not isinstance(data, dict):
                continue

            items = data.get("items")

            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                product_code = str(
                    item.get("product_code")
                    or item.get("raw_material_code")
                    or ""
                ).strip()
                branch = str(item.get("branch") or "").strip()
                warehouse = str(item.get("warehouse") or "").strip()
                key = (product_code, branch, warehouse)

                if key in seen:
                    continue

                seen.add(key)
                merged.append(dict(item))

        return merged
