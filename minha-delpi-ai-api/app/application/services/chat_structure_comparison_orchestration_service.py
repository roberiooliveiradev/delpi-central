from __future__ import annotations

from app.application.services.chat_structure_comparison_service import (
    ChatStructureComparisonService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class ChatStructureComparisonOrchestrationService:
    """Planeja consultas de estrutura (BOM) para comparação quando faltam dados no histórico."""

    @classmethod
    def plan_structure_fetches(
        cls,
        selection_service,
        *,
        message: str,
        allowed_action_ids: list[str] | None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        max_calls: int | None = None,
    ) -> list[dict]:
        if not ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            return []

        if not selection_service or not allowed_action_ids:
            return []

        limit = max(1, min(int(max_calls or 5), 8))
        snapshots, snapshot_order = ChatStructureComparisonService.collect_structure_snapshots(
            previous_messages or []
        )

        codes = ChatAnalysisIntentService.extract_all_product_codes(
            message,
            conversation_context,
        )

        if not codes and snapshot_order:
            codes = list(snapshot_order)

        if len(codes) < 2:
            return []

        complete = [
            code
            for code in codes
            if (snap := snapshots.get(code))
            and (snap.model is not None or snap.profile_lines)
        ]

        if len(complete) >= 2:
            return []

        to_fetch: list[str] = []

        for code in codes:
            snap = snapshots.get(code)

            if snap and snap.model is not None:
                continue

            to_fetch.append(code)

        if not to_fetch:
            to_fetch = [code for code in codes if code not in complete]

        planned: list[dict] = []

        for code in to_fetch[:limit]:
            selected = selection_service.select_action_for_product(
                message,
                product_code=code,
                allowed_action_ids=allowed_action_ids,
                intent=ChatProductQueryIntent.STRUCTURE,
            )

            if selected:
                planned.append(selected)

        return planned
