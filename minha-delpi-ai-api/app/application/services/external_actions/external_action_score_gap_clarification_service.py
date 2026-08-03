"""Clarificação quando top-2 do ranking lexical/semântico empatam (score-gap)."""

from __future__ import annotations

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionScoreGapClarificationService:
    @classmethod
    def clarification_tool_name(cls) -> str:
        return ExternalActionResponseContentService.get(
            "actionSelection",
            "scoreGap",
            "clarificationToolName",
            default="clarify_route_selection",
        )

    @classmethod
    def max_absolute_gap(cls) -> float:
        node = ExternalActionResponseContentService.get_node(
            "actionSelection",
            "scoreGap",
        )
        if not isinstance(node, dict):
            return 0.05
        try:
            return float(node.get("maxAbsoluteGap", 0.05))
        except (TypeError, ValueError):
            return 0.05

    @classmethod
    def is_clarification_tool_call(cls, tool_call: dict | None) -> bool:
        if not isinstance(tool_call, dict):
            return False
        return str(tool_call.get("name") or "") == cls.clarification_tool_name()

    @classmethod
    def maybe_build(cls, ranked: list[dict]) -> dict | None:
        """Se top-2 empatados, retorna tool call de clarificação; senão None."""
        if len(ranked) < 2:
            return None

        top = ranked[0]
        rival = ranked[1]
        score_a = top.get("selectionScore")
        score_b = rival.get("selectionScore")

        if score_a is None or score_b is None:
            return None

        try:
            gap = abs(float(score_a) - float(score_b))
        except (TypeError, ValueError):
            return None

        if gap > cls.max_absolute_gap():
            return None

        label_a = cls._label(top)
        label_b = cls._label(rival)
        operation_a = str(top.get("operationId") or top.get("actionId") or "").strip()
        operation_b = str(rival.get("operationId") or rival.get("actionId") or "").strip()

        direct_answer = ExternalActionResponseContentService.format(
            "actionSelection",
            "routeClarification",
            "scoreGapDirectAnswer",
            labelA=label_a,
            labelB=label_b,
            operationIdA=operation_a or "—",
            operationIdB=operation_b or "—",
        )

        return {
            "name": cls.clarification_tool_name(),
            "arguments": {
                "directAnswer": direct_answer,
                "scoreGap": round(gap, 4),
                "rivalIds": [
                    str(top.get("actionId") or ""),
                    str(rival.get("actionId") or ""),
                ],
                "operationIds": [operation_a, operation_b],
                "suggestions": [
                    {
                        "label": label_a,
                        "query": label_a,
                        "operationId": operation_a,
                    },
                    {
                        "label": label_b,
                        "query": label_b,
                        "operationId": operation_b,
                    },
                ],
            },
            "reason": ExternalActionResponseContentService.get(
                "selectionReasons",
                "scoreGapClarification",
                default="Empate no ranking de rotas OpenAPI — clarificação ao usuário.",
            ),
        }

    @classmethod
    def _label(cls, action: dict) -> str:
        summary = str(action.get("summary") or "").strip()
        if summary:
            return summary
        path = str(action.get("path") or "").strip()
        if path:
            return path
        return str(action.get("operationId") or action.get("actionId") or "rota").strip()
