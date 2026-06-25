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



class ChatOperationalDataCommentaryStatusService:
    @classmethod
    def _build_production_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        _ = format_quantity
        profile = "productionStatus"
        reference_date = str(root.get("reference_date") or "").strip()
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        items = root.get("items") if isinstance(root.get("items"), list) else []
        highlights: list[str] = []
        attention: list[str] = []

        pa_started = _Narrative.format_production_flag(summary.get("pa_production_started"))
        pi_started = _Narrative.format_production_flag(summary.get("pi_production_started"))
        pa_started_flag = _Narrative.is_production_started(summary.get("pa_production_started"))
        pi_started_flag = _Narrative.is_production_started(summary.get("pi_production_started"))
        total_orders = int(summary.get("total_pa_orders") or 0) + int(
            summary.get("total_pi_orders") or 0
        )
        reported_pa = _OpsTable.parse_quantity(summary.get("total_pa_reported_quantity") or 0)
        reported_pi = _OpsTable.parse_quantity(summary.get("total_pi_reported_quantity") or 0)

        if reference_date and summary:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "quickSummaryLine",
                    date=reference_date,
                    paStarted=pa_started,
                    piStarted=pi_started,
                    paQty=str(summary.get("total_pa_reported_quantity") or 0),
                )
            )
        elif reference_date:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(profile, "scopeHeadline", date=reference_date)
            )

        appointment_count = sum(
            1
            for item in items
            if isinstance(item, dict) and int(item.get("total_reports") or 0) > 0
        )

        if appointment_count:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(profile, "hasAppointments", count=str(appointment_count))
            )

        if total_orders > 0 and not pa_started_flag and not pi_started_flag:
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionStaleOp"))
        elif pi_started_flag and not pa_started_flag:
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "piWithoutPa"))

        if total_orders > 0 and reported_pa + reported_pi <= 0:
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionLowReport"))

        commentary: dict[str, Any] = {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "periodScoped": bool(reference_date),
        }

        return commentary

    @classmethod
    def _build_shipping_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        _ = format_quantity
        profile = "shippingStatus"
        date_start = str(root.get("date_start") or "").strip()
        date_end = str(root.get("date_end_exclusive") or "").strip()
        period = f"{date_start} → {date_end}".strip(" →")
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        highlights: list[str] = []
        attention: list[str] = []

        if period:
            highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "scopeHeadline", period=period))

        shipped = _OpsTable.parse_quantity(summary.get("total_shipped_quantity") or 0)
        loss = _OpsTable.parse_quantity(summary.get("total_inspection_loss_quantity") or 0)

        if shipped > 0:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(profile, "hasShipped", quantity=str(int(shipped) if shipped.is_integer() else shipped))
            )

        if loss > 0 and shipped <= 0:
            highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "lossWithoutShip"))
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionLossOnly"))
        elif shipped <= 0 and loss <= 0:
            highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "noMovement"))

        if loss > 0 and shipped > 0 and loss >= shipped * 0.2:
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionHighLoss"))

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "periodScoped": bool(period),
        }

    @classmethod
    def _build_directives_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        _ = format_quantity
        profile = "directives"
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        raw_materials = root.get("raw_materials") if isinstance(root.get("raw_materials"), list) else []
        highlights: list[str] = []
        attention: list[str] = []

        if summary:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "summaryLine",
                    raw_materials=str(summary.get("total_raw_materials") or len(raw_materials)),
                    suppliers=str(summary.get("total_supplier_links") or 0),
                    with_purchase=str(summary.get("raw_materials_with_last_purchase") or 0),
                    without_purchase=str(summary.get("raw_materials_without_last_purchase") or 0),
                )
            )

        without_purchase = int(summary.get("raw_materials_without_last_purchase") or 0)

        if without_purchase > 0:
            attention.append(
                ChatOperationalDataCommentarySupportService._text(profile, "attentionWithoutPurchase", count=str(without_purchase))
            )

        if not highlights and not attention:
            return {}

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "alertLevel": "attention" if attention else "ok",
        }

