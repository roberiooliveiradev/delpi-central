"""Explicação textual de dashboards — Playbook 09 Fase 5."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_chart_explain_service import (
    ChatPresentationChartExplainService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationDashboardExplainService:
    @classmethod
    def build(
        cls,
        *,
        presentation: dict[str, Any] | None,
        decision: dict[str, Any] | None = None,
        insight: str | None = None,
    ) -> str:
        vocab = ChatPresentationVocabularyService

        if not isinstance(presentation, dict) or presentation.get("type") != "dashboard":
            return ""

        panels = presentation.get("panels") or []

        if not isinstance(panels, list) or not panels:
            return vocab.dashboard_explain_text("emptyPanels")

        parts: list[str] = []
        insight_text = str(insight or (decision or {}).get("insight") or "").strip()

        if insight_text:
            parts.append(insight_text)

        title = str(
            presentation.get("title") or vocab.dashboard_explain_text("defaultTitle")
        ).strip()
        parts.append(
            vocab.dashboard_explain_text(
                "overview",
                title=title,
                panelCount=len(panels),
            )
        )

        for panel in panels:
            if not isinstance(panel, dict):
                continue

            panel_title = str(
                panel.get("title")
                or panel.get("id")
                or vocab.dashboard_explain_text("panelFallbackTitle")
            ).strip()
            block = panel.get("presentation")

            if not isinstance(block, dict):
                continue

            token = str(block.get("type") or "").strip().lower()

            if token == "kpi":
                cards = block.get("cards") or []

                if isinstance(cards, list) and cards:
                    snippets = []

                    for card in cards[:4]:
                        if not isinstance(card, dict):
                            continue

                        label = str(
                            card.get("label")
                            or vocab.dashboard_explain_text("kpiCardFallbackLabel")
                        ).strip()
                        value = card.get("value")
                        unit = str(card.get("unit") or "").strip()
                        suffix = f" {unit}" if unit else ""

                        snippets.append(f"«{label}» = {value}{suffix}")

                    if snippets:
                        parts.append(
                            vocab.dashboard_explain_text(
                                "kpiPanelSummary",
                                panelTitle=panel_title,
                                snippets="; ".join(snippets),
                            )
                        )
                else:
                    parts.append(
                        vocab.dashboard_explain_text(
                            "kpiPanelEmpty",
                            panelTitle=panel_title,
                        )
                    )

            elif token == "chart":
                chart_explain = ChatPresentationChartExplainService.build(
                    presentation=block,
                    decision=decision,
                    insight=None,
                )

                if chart_explain:
                    parts.append(
                        vocab.dashboard_explain_text(
                            "chartPanelPrefix",
                            panelTitle=panel_title,
                            chartExplain=chart_explain,
                        )
                    )

            elif token == "table":
                rows = block.get("rows") or []
                count = len(rows) if isinstance(rows, list) else 0

                parts.append(
                    vocab.dashboard_explain_text(
                        "tablePanel",
                        panelTitle=panel_title,
                        rowCount=count,
                    )
                )

        parts.append(vocab.dashboard_explain_text("exportHint"))

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def enrich_panel_charts(
        cls,
        presentation: dict[str, Any],
        *,
        decision: dict[str, Any] | None = None,
    ) -> None:
        panels = presentation.get("panels")

        if not isinstance(panels, list):
            return

        for panel in panels:
            if not isinstance(panel, dict):
                continue

            block = panel.get("presentation")

            if not isinstance(block, dict) or block.get("type") != "chart":
                continue

            explanation = ChatPresentationChartExplainService.build(
                presentation=block,
                decision=decision,
                insight=str(panel.get("title") or ""),
            )

            if explanation:
                block["chartExplanation"] = explanation
