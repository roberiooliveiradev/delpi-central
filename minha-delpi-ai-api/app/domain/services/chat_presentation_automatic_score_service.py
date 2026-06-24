"""Scoring automático de formato — extraído de ChatPresentationDecisionService (jun/2026)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_decision_metadata_service import (
    ChatPresentationDecisionMetadataService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

_NATIVE_PRIMARY_VIEWS = frozenset(
    {
        "table",
        "tree",
        "chart",
        "kpi",
        "dashboard",
        "line_chart",
        "area_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
        "grouped_bar",
        "stacked_bar",
        "combo_chart",
        "histogram",
        "heatmap",
        "gauge",
        "scatter",
    }
)

_CHART_TYPE_TO_SELECTED = {
    "line": "line_chart",
    "multi_line": "line_chart",
    "area": "area_chart",
    "bar": "bar_chart",
    "horizontal_bar": "horizontal_bar",
    "donut": "donut",
    "pie": "donut",
    "grouped_bar": "grouped_bar",
    "stacked_bar": "stacked_bar",
    "combo": "combo_chart",
    "histogram": "histogram",
    "heatmap": "heatmap",
    "gauge": "gauge",
    "scatter": "scatter",
}


class ChatPresentationAutomaticScoreService:
    @classmethod
    def compute_scores(
        cls,
        *,
        data_shape: dict[str, Any] | None,
        available_views: list[str] | None = None,
        user_message: str | None = None,
    ) -> dict[str, int]:
        shape = data_shape if isinstance(data_shape, dict) else {}
        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())
        recommended = str(shape.get("recommended") or "").strip()
        row_count = int(shape.get("rows") or 0)

        scores: dict[str, int] = {
            "text": 25,
            "table": 20,
            "chart": 10,
            "tree": 5,
            "kpi": 10,
            "dashboard": 10,
            "canvas": 5,
        }

        if shape.get("hasDate") or recommended == "line_chart":
            scores["chart"] += 40
            scores["table"] += 10

        if shape.get("hasCategory") or recommended in {"horizontal_bar", "donut", "bar_chart"}:
            scores["chart"] += 45
            scores["table"] += 15

        if shape.get("hasHierarchy") or recommended == "tree":
            scores["tree"] += 50
            scores["text"] += 10

        if recommended == "kpi" or (row_count <= 1 and shape.get("hasNumeric")):
            scores["kpi"] += 40

        if row_count >= 8:
            scores["table"] += 35

        if row_count >= 20:
            scores["chart"] += 10

        if any(token in message for token in ("resumo", "status", "situação", "situacao", "como está")):
            scores["text"] += 30

        if any(token in message for token in ("ranking", "maiores", "top ", "concentração", "concentracao")):
            scores["chart"] += 25

        from app.domain.services.chat_presentation_view_intent_service import (
            ChatPresentationViewIntentService,
        )

        score_deltas = ChatPresentationViewIntentService.automatic_score_deltas(
            data_shape=shape,
            user_message=message,
        )
        scores["table"] += int(score_deltas.get("table") or 0)
        scores["chart"] = max(0, int(scores.get("chart") or 0) + int(score_deltas.get("chart") or 0))

        if any(token in message for token in ("relatório", "relatorio", "lousa", "canvas")):
            scores["canvas"] += 35
            scores["text"] += 10

        views = {
            str(view).strip().lower()
            for view in (available_views or [])
            if str(view or "").strip()
        }

        if views:
            for key in list(scores.keys()):
                if key not in views and scores[key] < 30:
                    scores[key] = 0

        return {key: min(value, 100) for key, value in scores.items() if value > 0}

    @classmethod
    def attach_scores_and_reading_layers(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        table_rows: list[dict[str, Any]] | None,
        user_message: str | None,
    ) -> None:
        from app.domain.services.chat_humanized_data_response_content_service import (
            ChatHumanizedDataResponseContentService,
        )

        shape_meta = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}
        analyzed = ChatPresentationDataShapeAnalyzer.analyze(rows=table_rows)
        merged_shape = {**analyzed, **shape_meta}

        decision["scores"] = cls.compute_scores(
            data_shape=merged_shape,
            available_views=decision.get("availableViews")
            if isinstance(decision.get("availableViews"), list)
            else None,
            user_message=user_message,
        )

        reading_layers = ChatHumanizedDataResponseContentService.get_node("readingLayers")

        if isinstance(reading_layers, dict) and reading_layers:
            decision["readingLayers"] = reading_layers

        message = ChatPresentationDecisionMetadataService.message_from_metadata(metadata)

        if message and not str(decision.get("message") or "").strip():
            decision["message"] = message

    @classmethod
    def ensure_purpose(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        user_message: str | None,
    ) -> None:
        if str(decision.get("purpose") or "").strip():
            return

        if not ChatPresentationDecisionMetadataService.metadata_has_visual(metadata):
            return

        message = str(user_message or "").strip()

        if message:
            decision["purpose"] = message[:240]
            return

        selected = str(decision.get("selected") or "table").strip().lower()
        bucket = cls.score_bucket_for_view(selected)
        purpose = ChatPresentationVocabularyService.purpose_default(bucket)

        if purpose:
            decision["purpose"] = purpose

    @classmethod
    def score_bucket_for_view(cls, view: str) -> str:
        token = str(view or "").strip().lower()

        if token in _NATIVE_PRIMARY_VIEWS and token not in {
            "table",
            "tree",
            "chart",
            "kpi",
            "dashboard",
            "text",
            "canvas",
            "checklist",
        }:
            return "chart"

        if token == "chart":
            return "chart"

        return token

    @classmethod
    def score_for_view(cls, view: str, scores: dict[str, int]) -> int:
        bucket = cls.score_bucket_for_view(view)

        return int(scores.get(bucket) or 0)

    @classmethod
    def resolve_chart_selected_token(
        cls,
        decision: dict[str, Any],
        available_views: list[str],
    ) -> str:
        views = [
            str(view).strip().lower()
            for view in available_views
            if str(view or "").strip()
        ]
        shape = decision.get("dataShape") if isinstance(decision.get("dataShape"), dict) else {}
        recommended = str(shape.get("recommended") or "").strip()
        mapped = _CHART_TYPE_TO_SELECTED.get(recommended, recommended)

        if mapped and mapped in views:
            return mapped

        for view in views:
            if cls.score_bucket_for_view(view) == "chart":
                return view

        return "chart"

    @classmethod
    def should_skip_automatic_score_selection(
        cls,
        *,
        metadata: dict[str, Any],
        effective_preference: str | None,
        user_message: str | None,
        path: str | None,
        entity: str | None,
        decision: dict[str, Any] | None = None,
    ) -> bool:
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        if effective_preference:
            return True

        if str(metadata.get("explicitSessionFormat") or "").strip():
            return True

        if ChatPresentationTextFirstPolicyService.should_default_to_text_only(
            path=path,
            entity=entity,
            explicit_format=None,
            user_message=user_message,
        ):
            return True

        if ChatPresentationTextFirstPolicyService.looks_like_integrated_stack_request(
            user_message,
        ):
            return True

        resolved_entity = entity or ChatPresentationDecisionMetadataService.resolve_entity(
            metadata,
            path=path,
        )

        from app.domain.services.chat_presentation_view_intent_service import (
            ChatPresentationViewIntentService,
        )

        if ChatPresentationViewIntentService.prefers_table_for_automatic(
            path=path,
            entity=resolved_entity,
            data_shape=(
                decision.get("dataShape")
                if isinstance(decision, dict) and isinstance(decision.get("dataShape"), dict)
                else None
            ),
            user_message=user_message,
            has_table=bool(metadata.get("tablePresentation"))
            or ChatPresentationDecisionMetadataService.metadata_has_visual(metadata),
        ):
            return True

        return False

    @classmethod
    def apply_automatic_score_selection(
        cls,
        decision: dict[str, Any],
        *,
        metadata: dict[str, Any],
        effective_preference: str | None,
        user_message: str | None,
        path: str | None,
        entity: str | None,
    ) -> None:
        if cls.should_skip_automatic_score_selection(
            metadata=metadata,
            effective_preference=effective_preference,
            user_message=user_message,
            path=path,
            entity=entity,
            decision=decision,
        ):
            return

        if str(decision.get("layoutMode") or "").strip().lower() == "stack":
            return

        scores = decision.get("scores")

        if not isinstance(scores, dict) or not scores:
            return

        views = [
            str(view).strip().lower()
            for view in (decision.get("availableViews") or [])
            if str(view or "").strip()
        ]

        if not views:
            return

        ranked = sorted(views, key=lambda view: cls.score_for_view(view, scores), reverse=True)
        best_view = ranked[0]
        best_score = cls.score_for_view(best_view, scores)

        if best_score < 30:
            return

        bucket = cls.score_bucket_for_view(best_view)
        selected = (
            cls.resolve_chart_selected_token(decision, views)
            if bucket == "chart"
            else best_view
        )

        if not ChatPresentationDecisionMetadataService.view_has_presentation(metadata, selected):
            for view in ranked:
                if view != selected and ChatPresentationDecisionMetadataService.view_has_presentation(
                    metadata,
                    view,
                ):
                    selected = view
                    bucket = cls.score_bucket_for_view(view)
                    break

        fallback_candidates = [view for view in ranked if view != best_view]
        fallback = fallback_candidates[0] if fallback_candidates else str(decision.get("fallback") or "text")

        if cls.score_bucket_for_view(fallback) == "chart" and bucket != "chart":
            fallback = "table" if "table" in views else fallback

        decision["selected"] = selected
        decision["fallback"] = fallback
        decision["reason"] = ChatPresentationVocabularyService.decision_reason("scoreAutomatic")
        decision["layoutMode"] = "single"
        decision["visualOrder"] = [selected]
