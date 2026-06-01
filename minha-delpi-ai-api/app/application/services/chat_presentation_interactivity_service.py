"""Chips pós-resposta para tabelas, gráficos e árvores — Playbook 07."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/interactivity")


class ChatPresentationInteractivityService:
    @classmethod
    def build_from_tool_calls(cls, tool_calls: list | None) -> list[dict[str, str]]:
        presentation_type = cls._detect_presentation_type(tool_calls)

        if not presentation_type:
            return []

        chip_labels = list(
            (_content().get("presentationChips") or {}).get(presentation_type) or []
        )
        queries = _content().get("presentationQueries") or {}
        suggestions: list[dict[str, str]] = []

        for label in chip_labels[:6]:
            template = str(queries.get(label) or label).strip()
            item: dict[str, str] = {"label": str(label), "query": template}

            if str(label).strip() == "Explique esse gráfico":
                item["inlineAction"] = "explain_chart"

            if str(label).strip() == "Explique esse painel":
                item["inlineAction"] = "explain_dashboard"

            suggestions.append(item)

        suggestions.extend(
            cls._chips_from_presentation_decision(tool_calls, queries=queries)
        )

        return cls._dedupe_suggestions(suggestions)[:8]

    @classmethod
    def _chips_from_presentation_decision(
        cls,
        tool_calls: list | None,
        *,
        queries: dict[str, Any],
    ) -> list[dict[str, str]]:
        output: list[dict[str, str]] = []

        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            decision = metadata.get("presentationDecision")

            if not isinstance(decision, dict):
                continue

            selected = str(decision.get("selected") or "").strip().lower()
            views = decision.get("availableViews") or []

            if not isinstance(views, list):
                continue

            normalized_views = {
                str(view or "").strip().lower()
                for view in views
                if str(view or "").strip()
            }

            if selected != "table" and "table" in normalized_views:
                label = "Ver como tabela"
                output.append(
                    {
                        "label": label,
                        "query": str(queries.get(label) or "mostre o último resultado em tabela"),
                    }
                )

            if selected not in {"chart", "line_chart", "horizontal_bar", "donut"} and (
                "chart" in normalized_views
                or "line_chart" in normalized_views
            ):
                label = "Gerar gráfico"
                output.append(
                    {
                        "label": label,
                        "query": str(queries.get(label) or "gere um gráfico com os dados acima"),
                    }
                )

            break

        return output

    @staticmethod
    def _dedupe_suggestions(suggestions: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        output: list[dict[str, str]] = []

        for item in suggestions:
            label = str(item.get("label") or "").strip()

            if not label or label in seen:
                continue

            seen.add(label)
            output.append(item)

        return output

    @classmethod
    def _detect_presentation_type(cls, tool_calls: list | None) -> str | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            presentation = metadata.get("presentation")

            if not isinstance(presentation, dict):
                continue

            token = str(presentation.get("type") or "").strip().lower()

            if token in {"table", "chart", "tree", "kpi", "dashboard"}:
                return token

        return None
