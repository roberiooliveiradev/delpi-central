"""Recipes tipadas de layout/tema TV para VISTA (ops PresentationMutation)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tv_app.domain.presentation_intelligence.models import PresentationRecipeId

CONTENT_PATH = (
    Path(__file__).resolve().parents[3] / "content" / "presentation_recipes.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_presentation_recipes_cache() -> None:
    _load.cache_clear()


class PresentationRecipeService:
    """Projeta recipes → ops tipadas (background + frames/styles)."""

    @classmethod
    def document(cls) -> dict[str, Any]:
        raw = _load()
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def recipe_ids(cls) -> list[str]:
        recipes = cls.document().get("recipes")
        if not isinstance(recipes, dict):
            return []
        return sorted(str(key) for key in recipes.keys())

    @classmethod
    def get(cls, recipe_id: str) -> dict[str, Any] | None:
        recipes = cls.document().get("recipes")
        if not isinstance(recipes, dict):
            return None
        row = recipes.get(str(recipe_id or "").strip())
        return row if isinstance(row, dict) else None

    @classmethod
    def resolve_from_nl(cls, message: str) -> PresentationRecipeId | None:
        normalized = " ".join(str(message or "").strip().lower().split())
        if not normalized:
            return None
        recipes = cls.document().get("recipes")
        if not isinstance(recipes, dict):
            return None
        best: tuple[int, str, dict[str, Any]] | None = None
        for recipe_id, row in recipes.items():
            if not isinstance(row, dict):
                continue
            markers = row.get("markers")
            if not isinstance(markers, list):
                continue
            for marker in markers:
                token = str(marker or "").strip().lower()
                if token and token in normalized:
                    score = len(token)
                    if best is None or score > best[0]:
                        best = (score, str(recipe_id), row)
        if best is None:
            return None
        _, recipe_id, row = best
        theme = str(row.get("themeKey") or "").strip() or None
        labels = tuple(
            str(item).strip()
            for item in (row.get("labels") or [])
            if str(item).strip()
        )
        return PresentationRecipeId(recipe_id=recipe_id, theme_key=theme, labels=labels)

    @classmethod
    def ops_for_recipe(cls, recipe_id: str) -> list[dict[str, Any]]:
        recipe = cls.get(recipe_id)
        if not recipe:
            return []
        ops = recipe.get("ops")
        if not isinstance(ops, list):
            return []
        return [dict(op) for op in ops if isinstance(op, dict) and op.get("op")]

    @classmethod
    def catalog_projection(cls) -> dict[str, Any]:
        """Full compact projection (editor/tests). Prefer ``catalog_projection_for_actions`` for GPT."""
        doc = cls.document()
        recipes = doc.get("recipes") if isinstance(doc.get("recipes"), dict) else {}
        out: dict[str, Any] = {
            "principle": "TYPED_PRESENTATION_RECIPES",
            "summary": (
                "Use recipeId from this catalog for TV layout/theme. "
                "Emit the recipe ops (patch_native_config + upsert_block frames/styles). "
                "Never invent CSS outside typed style/frame/background."
            ),
            "fontFamilyAllowlist": list(doc.get("fontFamilyAllowlist") or []),
            "colorRamps": doc.get("colorRamps")
            if isinstance(doc.get("colorRamps"), dict)
            else {},
            "designTokens": doc.get("designTokens")
            if isinstance(doc.get("designTokens"), dict)
            else {},
            "recipes": {},
        }
        for recipe_id, row in recipes.items():
            if not isinstance(row, dict):
                continue
            out["recipes"][str(recipe_id)] = {
                "label": row.get("label"),
                "themeKey": row.get("themeKey"),
                "markers": row.get("markers") or [],
                "description": row.get("description"),
                "blueprint": row.get("blueprint") if isinstance(row.get("blueprint"), dict) else None,
            }
        return out

    @classmethod
    def catalog_projection_for_actions(cls) -> dict[str, Any]:
        """Byte-budget projection for ``gpt_get_catalog`` (GPT Actions ~100 KiB cap).

        Keeps recipe ids/markers + the designTokens the specialist must obey;
        drops bulky chrome defaults duplicated in ``shape_chrome`` / server VERIFY.
        """
        full = cls.catalog_projection()
        tokens = full.get("designTokens") if isinstance(full.get("designTokens"), dict) else {}
        part = tokens.get("partChrome") if isinstance(tokens.get("partChrome"), dict) else {}
        slim_part: dict[str, Any] = {}
        if isinstance(part.get("hierarchy"), dict):
            slim_part["hierarchy"] = part["hierarchy"]
        for family in ("kpi", "chart", "table", "input"):
            row = part.get(family)
            if isinstance(row, dict):
                # Keep only min/size gates — drop verbose default style blobs.
                slim_part[family] = {
                    k: v
                    for k, v in row.items()
                    if "Min" in str(k) or k in {"valueMinFontSize", "titleMinFontSize"}
                }
            slim_tokens: dict[str, Any] = {
            "maxPrimarySignalsPerSlide": tokens.get("maxPrimarySignalsPerSlide"),
            "safeMargin": tokens.get("safeMargin"),
            "typeScale": tokens.get("typeScale"),
            "typography": tokens.get("typography"),
            "spacing": tokens.get("spacing"),
            "brand": tokens.get("brand") if isinstance(tokens.get("brand"), dict) else {},
            "partChrome": slim_part,
            "chartTypeHints": tokens.get("chartTypeHints")
            if isinstance(tokens.get("chartTypeHints"), dict)
            else {},
            "visualImpactHints": tokens.get("visualImpactHints")
            if isinstance(tokens.get("visualImpactHints"), dict)
            else {},
        }
        recipes_out: dict[str, Any] = {}
        raw_recipes = full.get("recipes") if isinstance(full.get("recipes"), dict) else {}
        for recipe_id, row in raw_recipes.items():
            if not isinstance(row, dict):
                continue
            markers = row.get("markers") if isinstance(row.get("markers"), list) else []
            # Cap markers to keep catalog under Actions response budget.
            recipes_out[str(recipe_id)] = {
                "label": row.get("label"),
                "themeKey": row.get("themeKey"),
                "markers": markers[:8],
                "blueprint": row.get("blueprint") if isinstance(row.get("blueprint"), dict) else None,
            }
        return {
            "principle": full.get("principle"),
            "summary": full.get("summary"),
            "fontFamilyAllowlist": full.get("fontFamilyAllowlist") or [],
            "colorRamps": full.get("colorRamps")
            if isinstance(full.get("colorRamps"), dict)
            else {},
            "designTokens": slim_tokens,
            "recipes": recipes_out,
        }
