"""Compõe visuais de enrichment (wave-2) no renderPlan do primary.

Garante que o contrato de apresentação do primary continue a listagem/tabela
principal e incorpore indicadores complementares do enrichment, sem o MFE
tratar o follow-up como bolha dominante.
"""

from __future__ import annotations

from typing import Any

_VISUAL_KINDS = frozenset({"table", "kpi", "chart", "tree", "dashboard", "download"})
_SOURCE_BY_KIND = {
    "table": "tablePresentation",
    "kpi": "kpiPresentation",
    "chart": "chartPresentation",
    "tree": "treePresentation",
    "dashboard": "dashboardPresentation",
}


class ChatPresentationEnrichmentCompositionService:
    @classmethod
    def compose_into_primary(cls, tool_calls: list[Any] | None) -> None:
        if not isinstance(tool_calls, list) or len(tool_calls) < 2:
            return

        primary_meta: dict[str, Any] | None = None
        enrichment_metas: list[dict[str, Any]] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            role = str(metadata.get("compositionRole") or "").strip().lower()

            if role == "enrichment":
                enrichment_metas.append(metadata)
                continue

            if primary_meta is None:
                primary_meta = metadata

        if primary_meta is None or not enrichment_metas:
            return

        plan = primary_meta.get("renderPlan")

        if not isinstance(plan, dict) or int(plan.get("version") or 0) != 1:
            return

        segments = list(plan.get("segments") or [])
        existing_kinds = {
            str(segment.get("kind") or "").strip().lower()
            for segment in segments
            if isinstance(segment, dict)
        }

        changed = False

        for enrichment_meta in enrichment_metas:
            enrichment_plan = enrichment_meta.get("renderPlan")

            if not isinstance(enrichment_plan, dict):
                continue

            for segment in enrichment_plan.get("segments") or []:
                if not isinstance(segment, dict):
                    continue

                kind = str(segment.get("kind") or "").strip().lower()

                if kind not in _VISUAL_KINDS or kind in existing_kinds:
                    continue

                source_key = _SOURCE_BY_KIND.get(kind)

                if source_key and isinstance(enrichment_meta.get(source_key), dict):
                    primary_meta.setdefault(source_key, enrichment_meta.get(source_key))

                segments.append(dict(segment))
                existing_kinds.add(kind)
                changed = True

            # Neutraliza plan do enrichment para não competir com o primary no MFE.
            enrichment_meta["renderPlan"] = {
                "version": 1,
                "layoutMode": "single",
                "segments": [
                    {
                        "kind": "markdown",
                        "slot": "lead",
                        "source": "assistantMessage",
                    }
                ],
            }

        if not changed:
            return

        visual_count = sum(1 for kind in existing_kinds if kind in _VISUAL_KINDS)

        if visual_count > 1:
            plan["layoutMode"] = "stack"
            decision = primary_meta.get("presentationDecision")

            if isinstance(decision, dict):
                decision["layoutMode"] = "stack"

        plan["segments"] = segments
        primary_meta["renderPlan"] = plan
