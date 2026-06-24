"""Política visual por rota — ordem, estoque, árvore e tabela nativa."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationRouteVisualPolicyService:
    @classmethod
    def apply(cls, metadata: dict[str, Any], decision: dict[str, Any]) -> None:
        from app.domain.services.chat_presentation_route_policy_service import (
            ChatPresentationRoutePolicyService,
        )

        path = str(metadata.get("path") or "")
        views = list(decision.get("availableViews") or [])

        if views:
            ChatPresentationRoutePolicyService.apply_visual_order(
                decision,
                path=path,
                metadata=metadata,
            )

        has_tree = bool(
            ChatPresentationDecisionMetadataService.effective_tree_presentation(
                tree_presentation=metadata.get("treePresentation"),
                primary_presentation=metadata.get("presentation"),
            )
        )

        preferred = str(metadata.get("preferredFormat") or "").strip().lower()

        if (
            has_tree
            and preferred == "tree"
            and ChatPresentationRoutePolicyService.is_tree_route(path)
            and not ChatPresentationRoutePolicyService.is_analyser_route(path)
            and decision.get("selected") in {None, "text", "table"}
        ):
            decision["selected"] = "tree"
            decision["reason"] = ChatPresentationVocabularyService.decision_reason(
                "treePrimaryView",
            )

        if (
            ChatPresentationRoutePolicyService.is_stock_route(path)
            and preferred in {"chart", "table", "tree"}
            and preferred in set(views)
            and str(decision.get("selected") or "").strip().lower() != "text"
            and str(decision.get("layoutMode") or "").strip().lower() != "stack"
        ):
            decision["selected"] = preferred

            if preferred == "chart":
                decision["reason"] = ChatPresentationVocabularyService.route_policy_reason(
                    "stockChart",
                )
            elif preferred == "table":
                decision["reason"] = ChatPresentationVocabularyService.route_policy_reason(
                    "stockTable",
                )
            else:
                decision["reason"] = ChatPresentationVocabularyService.decision_reason(
                    "treePrimaryView",
                )

        if (
            ChatPresentationRoutePolicyService.is_table_route(path)
            and not ChatPresentationRoutePolicyService.is_tree_route(path)
            and not ChatPresentationRoutePolicyService.is_analyser_route(path)
            and preferred == "table"
            and "table" in views
        ):
            decision["selected"] = "table"
            decision["reason"] = ChatPresentationVocabularyService.decision_reason(
                "operationalTableNative",
            )
