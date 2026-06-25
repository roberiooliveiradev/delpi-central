"""Delegate — comentário operacional."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_constants import (
    CONTENT_SECTION as _CONTENT_SECTION,
    MP_LOW_COVERAGE_PA_THRESHOLD as _MP_LOW_COVERAGE_PA_THRESHOLD,
    PROFILE_CONTENT_MAP as _PROFILE_CONTENT_MAP,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_facade_access import (
    commentary_service,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)

_Narrative = ExternalActionOperationalRouteNarrativeService



class ChatOperationalDataCommentaryStockService:
    @classmethod
    def _build_stock_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        items = ChatOperationalDataCommentaryStockService._resolve_stock_items(root)
        agg = ChatOperationalDataCommentaryStockService._aggregate_stock(items, root)
        profile = "stock"
        highlights = ChatOperationalDataCommentaryStockService._build_stock_highlights(agg, format_quantity=format_quantity)
        attention = ChatOperationalDataCommentaryStockService._build_stock_attention(agg)

        commentary: dict[str, Any] = {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
        }

        if (
            agg.get("total_records") is not None
            and int(agg.get("positions") or 0) < int(agg.get("total_records") or 0)
        ):
            commentary["paginated"] = True

        return commentary

    @classmethod
    def _resolve_stock_items(cls, root: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(root.get("items"), list):
            return [item for item in root["items"] if isinstance(item, dict)]

        data = root.get("data")

        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [item for item in data["items"] if isinstance(item, dict)]

        return []

    @classmethod
    def _aggregate_stock(cls, items: list[dict[str, Any]], root: dict[str, Any]) -> dict[str, Any]:
        total_available = 0.0
        total_committed = 0.0
        has_available = False
        negative_positions = 0
        zero_available_positions = 0
        committed_over_current_positions = 0
        branch_available: dict[str, float] = {}

        for item in items:
            available_raw = item.get("available_quantity")
            current_raw = item.get("current_quantity")
            committed_raw = item.get("committed_quantity")
            available = (
                _OpsTable.parse_quantity(available_raw) if available_raw is not None else None
            )
            current = _OpsTable.parse_quantity(current_raw) if current_raw is not None else None
            committed = _OpsTable.parse_quantity(committed_raw or 0)
            branch = str(item.get("branch") or "").strip()

            if available is not None:
                has_available = True
                total_available += available

                if branch:
                    branch_available[branch] = branch_available.get(branch, 0.0) + available

                if available < 0:
                    negative_positions += 1

                if available == 0:
                    zero_available_positions += 1

            if current is not None and committed > current:
                committed_over_current_positions += 1

            total_committed += committed

        top_branch = ""
        top_branch_available = 0.0

        if branch_available:
            top_branch, top_branch_available = max(
                branch_available.items(),
                key=lambda pair: pair[1],
            )

        meta = root if isinstance(root, dict) else {}

        if isinstance(meta.get("data"), dict):
            meta = meta["data"]

        total_records = meta.get("total")

        return {
            "positions": len(items),
            "total_available": total_available,
            "total_committed": total_committed,
            "has_available": has_available,
            "negative_positions": negative_positions,
            "zero_available_positions": zero_available_positions,
            "committed_over_current_positions": committed_over_current_positions,
            "top_branch": top_branch,
            "top_branch_available": top_branch_available,
            "total_records": int(total_records) if total_records is not None else None,
        }

    @classmethod
    def _build_stock_highlights(cls,
        agg: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> list[str]:
        profile = "stock"
        highlights: list[str] = []

        def fmt(value: Any) -> str:
            if format_quantity:
                return format_quantity(value, "available_quantity")

            return str(value)

        if agg.get("has_available"):
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "headlineAvailable",
                    total=fmt(agg.get("total_available")),
                    positions=str(agg.get("positions") or 0),
                )
            )

        if float(agg.get("total_available") or 0) < 0:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "negativeTotal",
                    total=fmt(agg.get("total_available")),
                )
            )

        top_branch = str(agg.get("top_branch") or "").strip()

        if top_branch and float(agg.get("top_branch_available") or 0) != 0:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "topBranch",
                    branch=top_branch,
                    quantity=fmt(agg.get("top_branch_available")),
                )
            )

        if int(agg.get("zero_available_positions") or 0):
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "zeroPositions",
                    count=str(agg.get("zero_available_positions")),
                )
            )

        if int(agg.get("committed_over_current_positions") or 0):
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "committedOverCurrent",
                    count=str(agg.get("committed_over_current_positions")),
                )
            )

        return highlights

    @classmethod
    def _build_stock_attention(cls, agg: dict[str, Any]) -> list[str]:
        profile = "stock"
        attention: list[str] = []

        if float(agg.get("total_available") or 0) < 0 or int(agg.get("negative_positions") or 0):
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionNegative"))

        if int(agg.get("committed_over_current_positions") or 0):
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionCommitted"))

        if (
            float(agg.get("total_committed") or 0) > 0
            and agg.get("has_available")
            and float(agg.get("total_available") or 0) <= 0
        ):
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionFullyCommitted"))

        return attention

