"""Contratos internos de join / formato / recipe (não são GPT Actions)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class JoinPlanProposal:
    """Proposta determinística de merge tipado entre duas fontes."""

    left_key: str
    right_key: str
    confidence: float
    diagnostics: tuple[str, ...] = ()
    join: str = "left"

    def to_dict(self) -> dict[str, Any]:
        return {
            "leftKey": self.left_key,
            "rightKey": self.right_key,
            "confidence": self.confidence,
            "diagnostics": list(self.diagnostics),
            "join": self.join,
            "mergeStep": {
                "op": "merge",
                "leftKey": self.left_key,
                "rightKey": self.right_key,
                "join": self.join,
            },
        }

    @property
    def is_usable(self) -> bool:
        return bool(self.left_key and self.right_key and self.confidence >= 0.55)


@dataclass(frozen=True, slots=True)
class FormatHint:
    """Sugestão de formatação alinhada ao DisplayFormatSpec / valueFormat legado."""

    category: str
    value_format: str
    currency: str | None = None
    decimal_places: int | None = None
    source: str = "nl"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "category": self.category,
            "valueFormat": self.value_format,
            "source": self.source,
        }
        if self.currency:
            payload["currency"] = self.currency
        if self.decimal_places is not None:
            payload["decimalPlaces"] = self.decimal_places
        return payload

    def display_format_spec(self) -> dict[str, Any]:
        spec: dict[str, Any] = {
            "category": self.category,
            "locale": "pt-BR",
        }
        if self.currency:
            spec["currency"] = self.currency
        if self.decimal_places is not None:
            spec["decimalPlaces"] = self.decimal_places
        if self.category == "currency":
            spec["presetId"] = "currency-brl"
        return spec

    def kpi_options_patch(self) -> dict[str, Any]:
        return {
            "valueFormat": self.value_format,
            "displayValueFormat": self.display_format_spec(),
            **(
                {"decimalPlaces": self.decimal_places}
                if self.decimal_places is not None
                else {}
            ),
        }


@dataclass(frozen=True, slots=True)
class PresentationRecipeId:
    """Identificador de recipe tipada de layout/tema TV."""

    recipe_id: str
    theme_key: str | None = None
    labels: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipeId": self.recipe_id,
            "themeKey": self.theme_key,
            "labels": list(self.labels),
        }
