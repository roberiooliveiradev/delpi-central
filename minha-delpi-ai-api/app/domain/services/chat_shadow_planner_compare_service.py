"""Shadow planner compare — decide em paralelo sem write duplicado."""

from __future__ import annotations

from typing import Any


class ChatShadowPlannerCompareService:
    """Compara decisões baseline × candidate sem executar writes."""

    WRITE_HINTS = ("post", "put", "patch", "delete")

    @classmethod
    def summarize_decision(cls, tool_calls: list[dict[str, Any]] | None) -> dict[str, Any]:
        actions: list[dict[str, Any]] = []
        for item in tool_calls or []:
            if not isinstance(item, dict):
                continue
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            args = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
            method = str(meta.get("method") or "").strip().lower()
            actions.append(
                {
                    "name": item.get("name"),
                    "actionId": args.get("actionId") or meta.get("actionId"),
                    "path": meta.get("path"),
                    "goalIds": meta.get("goalIds") or [],
                    "requestedPresentation": meta.get("requestedPresentation"),
                    "candidateSetId": meta.get("candidateSetId"),
                    "isWrite": method in cls.WRITE_HINTS
                    or bool(meta.get("requiresConfirmation")),
                }
            )
        return {
            "actionIds": [row.get("actionId") for row in actions if row.get("actionId")],
            "paths": [row.get("path") for row in actions if row.get("path")],
            "goalIds": sorted(
                {
                    goal_id
                    for row in actions
                    for goal_id in (row.get("goalIds") or [])
                    if goal_id
                }
            ),
            "requestedPresentation": next(
                (
                    row.get("requestedPresentation")
                    for row in actions
                    if row.get("requestedPresentation")
                ),
                None,
            ),
            "hasWrite": any(row.get("isWrite") for row in actions),
            "actions": actions,
        }

    @classmethod
    def compare(
        cls,
        *,
        baseline_tool_calls: list[dict[str, Any]] | None,
        candidate_tool_calls: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        baseline = cls.summarize_decision(baseline_tool_calls)
        candidate = cls.summarize_decision(candidate_tool_calls)
        return {
            "actionIdsMatch": baseline["actionIds"] == candidate["actionIds"],
            "pathsMatch": baseline["paths"] == candidate["paths"],
            "goalIdsMatch": baseline["goalIds"] == candidate["goalIds"],
            "presentationMatch": baseline["requestedPresentation"]
            == candidate["requestedPresentation"],
            "baselineHasWrite": baseline["hasWrite"],
            "candidateHasWrite": candidate["hasWrite"],
            "safeToDualExecute": not baseline["hasWrite"] and not candidate["hasWrite"],
            "baseline": baseline,
            "candidate": candidate,
        }
