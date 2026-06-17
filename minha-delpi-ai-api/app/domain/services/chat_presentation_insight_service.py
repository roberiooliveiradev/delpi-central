"""Insight curto para visualizações — Playbook 09 §16."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationInsightService:
    @classmethod
    def build(
        cls,
        *,
        selected: str | None,
        rows: list[dict[str, Any]] | None,
        data_shape: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> str:
        vocab = ChatPresentationVocabularyService
        token = str(selected or "").strip().lower()
        safe_rows = [row for row in (rows or []) if isinstance(row, dict)]
        shape = data_shape or {}

        tree_nodes = shape.get("treeNodes")

        if token == "tree":
            if tree_nodes is False or tree_nodes == 0:
                return ""

            return vocab.insight_text("tree")

        if not safe_rows:
            if shape.get("hasNarrative"):
                return ""

            return vocab.insight_text("insufficientData")

        if token in {"line_chart", "area_chart"}:
            return cls._temporal_insight(safe_rows, shape)

        if token in {"horizontal_bar", "bar_chart"}:
            return cls._ranking_insight(safe_rows, shape)

        if token in {"donut", "pie"}:
            return cls._participation_insight(safe_rows, shape)

        if token == "kpi":
            return vocab.insight_text("kpi")

        if token == "table":
            count = int(shape.get("rows") or len(safe_rows))

            return vocab.insight_text(
                "table",
                count=str(count),
                lineUnit=vocab.insight_table_line_unit(count),
            )

        if token in {"grouped_bar", "combo_chart", "stacked_bar"}:
            return vocab.insight_text("groupedSeries")

        fallback = str(reason or "").strip()

        if fallback:
            return fallback[0].upper() + fallback[1:] + "."

        return vocab.insight_text("controlsFallback")

    @classmethod
    def _temporal_insight(
        cls,
        rows: list[dict[str, Any]],
        shape: dict[str, Any],
    ) -> str:
        vocab = ChatPresentationVocabularyService
        label_key = shape.get("labelKey")
        numeric_keys = shape.get("numericKeys") or []
        value_key = numeric_keys[0] if numeric_keys else None

        if not label_key or not value_key:
            return vocab.insight_text("temporalDefault")

        values = [
            float(row.get(value_key))
            for row in rows
            if isinstance(row.get(value_key), (int, float))
        ]

        if len(values) < 2:
            return vocab.insight_text("temporalDefault")

        peak_index = max(range(len(values)), key=lambda index: values[index])
        low_index = min(range(len(values)), key=lambda index: values[index])
        peak_label = (
            str(rows[peak_index].get(label_key) or "").strip()
            or vocab.insight_text("temporalPeakFallback")
        )
        low_label = (
            str(rows[low_index].get(label_key) or "").strip()
            or vocab.insight_text("temporalLowFallback")
        )

        if peak_index == low_index:
            return vocab.insight_text("temporalPeakOnly", peakLabel=peak_label)

        return vocab.insight_text(
            "temporalPeakAndLow",
            peakLabel=peak_label,
            lowLabel=low_label,
        )

    @classmethod
    def _ranking_insight(
        cls,
        rows: list[dict[str, Any]],
        shape: dict[str, Any],
    ) -> str:
        vocab = ChatPresentationVocabularyService
        label_key = shape.get("labelKey")
        numeric_keys = shape.get("numericKeys") or []
        value_key = numeric_keys[0] if numeric_keys else None

        if not label_key or not value_key or not rows:
            return vocab.insight_text("rankingDefault")

        leader = max(
            rows,
            key=lambda row: float(row.get(value_key) or 0)
            if isinstance(row.get(value_key), (int, float))
            else 0,
        )
        leader_label = (
            str(leader.get(label_key) or "").strip()
            or vocab.insight_text("rankingLeaderFallback")
        )

        if len(rows) >= 3:
            return vocab.insight_text("rankingTopItems", leaderLabel=leader_label)

        return vocab.insight_text("rankingLeader", leaderLabel=leader_label)

    @classmethod
    def _participation_insight(
        cls,
        rows: list[dict[str, Any]],
        shape: dict[str, Any],
    ) -> str:
        vocab = ChatPresentationVocabularyService
        label_key = shape.get("labelKey")
        numeric_keys = shape.get("numericKeys") or []
        value_key = numeric_keys[0] if numeric_keys else None

        if not label_key or not value_key:
            return vocab.insight_text("participationDefault")

        leader = max(
            rows,
            key=lambda row: float(row.get(value_key) or 0)
            if isinstance(row.get(value_key), (int, float))
            else 0,
        )
        leader_label = (
            str(leader.get(label_key) or "").strip()
            or vocab.insight_text("participationLeaderFallback")
        )

        return vocab.insight_text("participationLeader", leaderLabel=leader_label)

    @classmethod
    def build_with_metadata(
        cls,
        *,
        selected: str | None,
        rows: list[dict[str, Any]] | None,
        data_shape: dict[str, Any] | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if isinstance(metadata, dict):
            from app.domain.services.chat_humanized_data_response_service import (
                ChatHumanizedDataResponseService,
            )

            commentary = ChatHumanizedDataResponseService.resolve_commentary_from_metadata(
                metadata,
            )

            if isinstance(commentary, dict):
                narrative = str(commentary.get("narrativeInsight") or "").strip()

                if narrative:
                    return narrative

                summary = commentary.get("summary")

                if isinstance(summary, dict):
                    answer = str(summary.get("answer") or "").strip()

                    if answer:
                        return answer
                elif isinstance(summary, str) and summary.strip():
                    return summary.strip()

            data_answer = metadata.get("dataAnswer")

            if isinstance(data_answer, dict):
                summary_block = data_answer.get("summary")

                if isinstance(summary_block, dict):
                    answer = str(summary_block.get("answer") or "").strip()

                    if answer:
                        return answer

        return cls.build(
            selected=selected,
            rows=rows,
            data_shape=data_shape,
            reason=reason,
        )
