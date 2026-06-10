"""Montagem de presentation tipo KPI a partir de cards — chat base (qualquer rota)."""

from __future__ import annotations

from typing import Any


class ChatPresentationKpiAssemblyService:
    """Contrato único de KPI consumido pelo MFE (`kpiPresentation` ou primário)."""

    _COUNT_LABEL_FRAGMENTS = (
        "componente",
        "ordem",
        "exclusiv",
        "tabela",
        "registro",
        "quantidade",
        "mp",
        "op",
        "unidade",
        "contagem",
        "count",
    )

    _CURRENCY_LABEL_FRAGMENTS = (
        "preco",
        "preço",
        "custo",
        "valor",
        "receita",
        "faturamento",
        "saldo",
    )

    @classmethod
    def build(
        cls,
        *,
        title: str,
        cards: list[dict[str, Any]],
        min_cards: int = 1,
    ) -> dict[str, Any] | None:
        normalized = [
            cls.normalize_card(card)
            for card in cards
            if isinstance(card, dict) and card.get("label") is not None
        ]

        if len(normalized) < min_cards:
            return None

        return {
            "type": "kpi",
            "title": str(title or "").strip() or "Indicadores",
            "cards": normalized[:8],
        }

    @classmethod
    def normalize_card(cls, card: dict[str, Any]) -> dict[str, Any]:
        payload = dict(card)
        existing_type = str(payload.get("dataType") or "").strip().lower()

        if existing_type in {
            "text",
            "number",
            "currency",
            "date",
            "percent",
            "quantity",
            "days",
        }:
            payload["dataType"] = existing_type
            return payload

        resolved_type = cls._infer_data_type(
            key=str(payload.get("key") or "").strip() or None,
            unit=str(payload.get("unit") or ""),
            label=str(payload.get("label") or "").strip() or None,
        )

        if resolved_type:
            payload["dataType"] = resolved_type

        return payload

    @classmethod
    def normalize_presentation(cls, presentation: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(presentation, dict):
            return presentation

        if str(presentation.get("type") or "").strip().lower() != "kpi":
            return presentation

        cards = presentation.get("cards")

        if not isinstance(cards, list):
            return presentation

        presentation["cards"] = [
            cls.normalize_card(card) for card in cards if isinstance(card, dict)
        ]

        return presentation

    @classmethod
    def normalize_metadata(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        for key in ("kpiPresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict):
                metadata[key] = cls.normalize_presentation(presentation)

        dashboard = metadata.get("dashboardPresentation")

        if not isinstance(dashboard, dict) or dashboard.get("type") != "dashboard":
            return

        panels = dashboard.get("panels")

        if not isinstance(panels, list):
            return

        for panel in panels:
            if not isinstance(panel, dict):
                continue

            nested = panel.get("presentation")

            if isinstance(nested, dict):
                panel["presentation"] = cls.normalize_presentation(nested)

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

        resolved_type = data_type or cls._infer_data_type(key=key, unit=unit, label=label)

        if resolved_type:
            card["dataType"] = resolved_type

        return card

    @classmethod
    def _infer_data_type(
        cls,
        *,
        key: str | None,
        unit: str,
        label: str | None = None,
    ) -> str | None:
        token = str(unit or "").strip()

        if token == "R$":
            return "currency"

        if token == "%":
            return "percent"

        if token in {"MP", "OP", "un."}:
            return "quantity"

        normalized_key = cls._normalize_token(key)
        normalized_label = cls._normalize_token(label)

        for text in (normalized_key, normalized_label):
            if not text:
                continue

            if any(fragment in text for fragment in cls._COUNT_LABEL_FRAGMENTS):
                return "quantity"

            if any(fragment in text for fragment in cls._CURRENCY_LABEL_FRAGMENTS):
                return "currency" if token == "R$" else "number"

        if normalized_key and any(
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

        if normalized_key and any(
            fragment in normalized_key
            for fragment in ("price", "cost", "valor", "sale", "discount", "revenue")
        ):
            return "currency" if token == "R$" else "number"

        if normalized_key or normalized_label:
            return "number"

        return None

    @classmethod
    def _normalize_token(cls, value: str | None) -> str:
        return (
            str(value or "")
            .strip()
            .lower()
            .replace("ã", "a")
            .replace("á", "a")
            .replace("â", "a")
            .replace("ç", "c")
            .replace("õ", "o")
            .replace("ó", "o")
            .replace("ê", "e")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ú", "u")
        )
