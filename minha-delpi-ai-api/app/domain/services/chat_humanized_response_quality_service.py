"""Checklist automatizado de respostas humanizadas — Playbook 13 §13."""

from __future__ import annotations

from typing import Any


class ChatHumanizedResponseQualityService:
    @classmethod
    def evaluate(cls, metadata: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(metadata, dict):
            return cls._empty_result(gaps=["metadata_invalid"])

        data_answer = metadata.get("dataAnswer")
        decision = metadata.get("presentationDecision") or {}
        gaps: list[str] = []
        checklist: dict[str, bool] = {}

        if not isinstance(data_answer, dict):
            checklist["starts_with_conclusion"] = False
            gaps.append("missing_data_answer")
            return cls._result(checklist=checklist, gaps=gaps)

        summary = data_answer.get("summary") or {}
        answer = str(summary.get("answer") or "").strip()
        meaning = str(summary.get("meaning") or "").strip()
        interpretation = str(data_answer.get("interpretation") or "").strip()

        checklist["starts_with_conclusion"] = bool(answer)
        if not answer:
            gaps.append("missing_summary_answer")

        checklist["important_numbers_interpreted"] = bool(
            meaning or interpretation or data_answer.get("derivedMetrics")
        )
        if answer and not checklist["important_numbers_interpreted"]:
            gaps.append("missing_interpretation_or_metrics")

        facts = data_answer.get("facts") or []
        analysis = data_answer.get("analysis") or []
        recommendations = data_answer.get("recommendations") or []

        checklist["fact_analysis_recommendation_separated"] = bool(
            facts or analysis or recommendations
        )

        attention = [
            str(line).strip()
            for line in (data_answer.get("attention") or [])
            if str(line or "").strip()
        ]
        anomalies = data_answer.get("anomalies") or []
        checklist["anomalies_in_attention"] = not anomalies or bool(attention)
        if anomalies and not attention:
            gaps.append("anomalies_without_attention")

        purpose = str(decision.get("purpose") or "").strip()
        has_visual = cls._has_visual_evidence(metadata)
        checklist["visual_has_purpose"] = not has_visual or bool(purpose)
        if has_visual and not purpose:
            gaps.append("visual_without_purpose")

        limitations = [
            str(line).strip()
            for line in (data_answer.get("limitations") or [])
            if str(line or "").strip()
        ]
        checklist["limitations_informed"] = bool(limitations)
        if not limitations:
            gaps.append("missing_limitations")

        rec_with_query = all(
            isinstance(item, dict)
            and str(item.get("label") or "").strip()
            and str(item.get("query") or "").strip()
            for item in recommendations
        ) if recommendations else True
        checklist["recommendations_clickable"] = rec_with_query
        if recommendations and not rec_with_query:
            gaps.append("recommendations_missing_query")

        scores = decision.get("scores") or {}
        checklist["scores_auditable"] = isinstance(scores, dict) and bool(scores)
        if has_visual and not scores:
            gaps.append("missing_presentation_scores")

        checklist["no_unconfirmed_hypothesis_as_fact"] = cls._hypotheses_not_affirmed_as_fact(
            analysis
        )
        if not checklist["no_unconfirmed_hypothesis_as_fact"]:
            gaps.append("unconfirmed_hypothesis_as_fact")

        return cls._result(checklist=checklist, gaps=gaps)

    @classmethod
    def evaluate_expectations(
        cls,
        metadata: dict[str, Any] | None,
        *,
        expect: dict[str, Any] | None,
    ) -> list[str]:
        if not expect:
            return []

        result = cls.evaluate(metadata)
        gaps: list[str] = []

        if expect.get("no_data_answer"):
            if isinstance(metadata, dict) and metadata.get("dataAnswer"):
                gaps.append("unexpected_data_answer")
            return gaps

        if expect.get("summary_answer") and not result["checklist"].get("starts_with_conclusion"):
            gaps.append("expected_summary_answer")

        if expect.get("limitations") and not result["checklist"].get("limitations_informed"):
            gaps.append("expected_limitations")

        if expect.get("recommendations_with_query") and not result["checklist"].get(
            "recommendations_clickable"
        ):
            data_answer = (metadata or {}).get("dataAnswer") or {}
            recs = data_answer.get("recommendations") or []

            if not recs:
                gaps.append("expected_recommendations")
            else:
                gaps.append("expected_recommendation_queries")

        if expect.get("derived_metrics"):
            data_answer = (metadata or {}).get("dataAnswer") or {}

            if not data_answer.get("derivedMetrics"):
                gaps.append("expected_derived_metrics")

        if expect.get("risk_undefined"):
            summary = ((metadata or {}).get("dataAnswer") or {}).get("summary") or {}
            risk = str(summary.get("riskLevel") or "").strip().lower()

            if risk and risk != "undefined":
                gaps.append(f"expected_risk_undefined got={risk}")

        return gaps

    @classmethod
    def _has_visual_evidence(cls, metadata: dict[str, Any]) -> bool:
        visual_keys = (
            "tablePresentations",
            "chartPresentation",
            "kpiPresentation",
            "treePresentation",
            "dashboardPresentation",
        )

        for key in visual_keys:
            value = metadata.get(key)

            if isinstance(value, list) and value:
                return True

            if isinstance(value, dict) and value:
                return True

        return False

    @classmethod
    def _hypotheses_not_affirmed_as_fact(cls, analysis: Any) -> bool:
        if not isinstance(analysis, list):
            return True

        for item in analysis:
            if not isinstance(item, dict):
                continue

            hypothesis = str(item.get("hypothesis") or "").strip()
            confirmed = item.get("confirmed")

            if hypothesis and confirmed is False and item.get("statedAsFact") is True:
                return False

        return True

    @classmethod
    def _empty_result(cls, *, gaps: list[str]) -> dict[str, Any]:
        return cls._result(checklist={}, gaps=gaps)

    @classmethod
    def _result(cls, *, checklist: dict[str, bool], gaps: list[str]) -> dict[str, Any]:
        return {
            "ok": not gaps,
            "checklist": checklist,
            "gaps": gaps,
            "gapCount": len(gaps),
        }
