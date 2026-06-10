"""Montagem de presentation tipo KPI a partir de cards — chat base (qualquer rota)."""

from __future__ import annotations

from typing import Any


class ChatPresentationKpiAssemblyService:
    """Contrato único de KPI consumido pelo MFE (`kpiPresentation` ou primário)."""

    @classmethod
    def build(
        cls,
        *,
        title: str,
        cards: list[dict[str, Any]],
        min_cards: int = 1,
    ) -> dict[str, Any] | None:
        normalized = [card for card in cards if isinstance(card, dict) and card.get("label") is not None]

        if len(normalized) < min_cards:
            return None

        return {
            "type": "kpi",
            "title": str(title or "").strip() or "Indicadores",
            "cards": normalized[:8],
        }

    @classmethod
    def metric_card(
        cls,
        *,
        label: str,
        value: object,
        unit: str = "",
        color: str = "#0ea5e9",
        key: str | None = None,
        trend: str | None = None,
        delta: str | None = None,
    ) -> dict[str, Any]:
        card: dict[str, Any] = {
            "label": str(label or "").strip(),
            "value": value,
            "unit": str(unit or "").strip(),
            "color": color,
        }

        if key:
            card["key"] = key

        if trend:
            card["trend"] = trend

        if delta:
            card["delta"] = delta

        return card
