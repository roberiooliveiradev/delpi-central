"""Diagnóstico de seleção de rota — matchSource / rivalIds / scoreGap."""

from __future__ import annotations

from typing import Any


class ExternalActionSelectionDiagnosticsService:
    @classmethod
    def annotate(
        cls,
        tool_call: dict | None,
        *,
        match_source: str,
        ranked: list[dict] | None = None,
        reason_key: str | None = None,
        top_n: int = 5,
    ) -> dict | None:
        if not isinstance(tool_call, dict):
            return tool_call

        enriched = dict(tool_call)
        diagnostics: dict[str, Any] = {
            "matchSource": str(match_source or "").strip() or "unknown",
        }

        if reason_key:
            diagnostics["reasonKey"] = str(reason_key).strip()

        if ranked:
            top = ranked[: max(1, top_n)]
            rival_ids = [
                str(item.get("actionId") or item.get("operationId") or "").strip()
                for item in top
                if str(item.get("actionId") or item.get("operationId") or "").strip()
            ]
            diagnostics["rivalIds"] = rival_ids

            scores: list[float] = []
            for item in top[:2]:
                raw = item.get("selectionScore")
                if raw is None:
                    continue
                try:
                    scores.append(float(raw))
                except (TypeError, ValueError):
                    continue
            if len(scores) >= 2:
                diagnostics["scoreGap"] = round(abs(scores[0] - scores[1]), 4)
            elif len(scores) == 1:
                diagnostics["scoreGap"] = None

        arguments = dict(enriched.get("arguments") or {})
        meta = dict(arguments.get("selectionDiagnostics") or {})
        meta.update(diagnostics)
        arguments["selectionDiagnostics"] = meta
        enriched["arguments"] = arguments
        enriched["selectionDiagnostics"] = meta
        return enriched

    @classmethod
    def from_tool_call(cls, tool_call: dict | None) -> dict[str, Any]:
        if not isinstance(tool_call, dict):
            return {}
        direct = tool_call.get("selectionDiagnostics")
        if isinstance(direct, dict):
            return dict(direct)
        arguments = tool_call.get("arguments")
        if isinstance(arguments, dict):
            nested = arguments.get("selectionDiagnostics")
            if isinstance(nested, dict):
                return dict(nested)
        return {}
