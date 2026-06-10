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
        data_type: str | None = None,
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

        resolved_type = data_type or cls._infer_data_type(key=key, unit=unit)

        if resolved_type:
            card["dataType"] = resolved_type

        return card

    @classmethod
    def _infer_data_type(cls, *, key: str | None, unit: str) -> str | None:
        token = str(unit or "").strip()

        if token == "R$":
            return "currency"

        if token == "%":
            return "percent"

        if token in {"MP", "OP", "un."}:
            return "quantity"

        normalized_key = str(key or "").strip().lower()

        if not normalized_key:
            return None

        if any(
            fragment in normalized_key
            for fragment in (
                "component",
                "order",
                "exclusive",
                "without_stock",
                "shipped",
                "price_table",
                "tables",
                "quantity",
                "count",
            )
        ):
            return "quantity"

        if any(
            fragment in normalized_key
            for fragment in ("price", "cost", "valor", "sale", "discount", "revenue")
        ):
            return "currency" if token == "R$" else "number"

        return "number"
