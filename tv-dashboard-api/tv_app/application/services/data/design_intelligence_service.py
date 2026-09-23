"""Structured design intelligence projected to VISTA (catalog authority)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)

_CONTENT = Path(__file__).resolve().parents[3] / "content" / "design_intelligence.json"

_LABEL_KEYS = frozenset({"label", "bucket", "periodo", "date", "name", "categoria", "category"})
_TEMPORAL_KEYS = frozenset({"date", "bucket", "periodo", "competencia", "granularity"})
_GOAL_HINTS = ("target", "goal", "meta", "objetivo")
_PERCENT_HINTS = ("pct", "percent", "rate", "taxa", "conversion")
_CURRENCY_HINTS = ("revenue", "receita", "valor", "amount", "brl")


@lru_cache(maxsize=1)
def _document() -> dict[str, Any]:
    raw = json.loads(_CONTENT.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


class DesignIntelligenceService:
    @classmethod
    def catalog_projection(cls) -> dict[str, Any]:
        doc = _document()
        return {
            "version": doc.get("version"),
            "componentSpecs": doc.get("componentSpecs") or {},
            "authority": "design_intelligence.json",
        }

    @classmethod
    def semantic_digest(
        cls,
        rows: list[Mapping[str, Any]] | None,
        *,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        typed = [row for row in (rows or []) if isinstance(row, Mapping)]
        names = list(columns or [])
        if not names and typed:
            names = [str(key) for key in typed[0].keys()]
        fields: list[dict[str, Any]] = []
        temporal = {"detected": False}
        category_cardinality: dict[str, int] = {}
        ranking: list[str] = []
        goals: list[str] = []
        composition: list[str] = []
        trends: list[str] = []
        for name in names:
            sample = next((row.get(name) for row in typed if name in row), None)
            role = _role_for(name, sample)
            unit = _unit_for(name, sample)
            cardinality = None
            if role in {"category", "dimension"} and typed:
                cardinality = len({str(row.get(name)) for row in typed if row.get(name) is not None})
                category_cardinality[name] = cardinality
                if cardinality and cardinality > 4:
                    ranking.append(name)
                if cardinality and cardinality <= 5:
                    composition.append(name)
            if role == "temporal":
                temporal = {"detected": True, "field": name}
                trends.append(name)
            if role == "goal":
                goals.append(name)
            if role == "metric" and temporal.get("detected"):
                trends.append(name)
            fields.append(
                {
                    "name": name,
                    "role": role,
                    "dataType": _data_type(sample),
                    "unit": unit,
                    "cardinality": cardinality,
                }
            )
        return {
            "fields": fields,
            "rowCount": len(typed),
            "temporal": temporal,
            "categoryCardinality": category_cardinality,
            "rankingCandidates": ranking,
            "goalCandidates": goals,
            "compositionCandidates": composition,
            "trendCandidates": trends,
        }

    @classmethod
    def _recommend(cls, digest: Mapping[str, Any]) -> dict[str, Any]:
        temporal = digest.get("temporal") if isinstance(digest.get("temporal"), dict) else {}
        ranking = digest.get("rankingCandidates") if isinstance(digest.get("rankingCandidates"), list) else []
        goals = digest.get("goalCandidates") if isinstance(digest.get("goalCandidates"), list) else []
        composition = (
            digest.get("compositionCandidates")
            if isinstance(digest.get("compositionCandidates"), list)
            else []
        )
        rejected: list[dict[str, str]] = []
        alternatives: list[dict[str, str]] = []
        if temporal.get("detected"):
            rejected.append({"type": "pie", "reason": "temporal series is not a composition"})
            rejected.append({"type": "doughnut", "reason": "temporal series is not a composition"})
            return {
                "recommendedType": "line",
                "confidence": 0.86,
                "reasons": ["temporal dimension plus metric"],
                "alternatives": [{"type": "area", "reason": "same trend, filled"}],
                "rejected": rejected,
            }
        if goals:
            return {
                "recommendedType": "gauge",
                "confidence": 0.8,
                "reasons": ["metric and goal present"],
                "alternatives": [{"type": "kpi_view", "reason": "hero KPI with progress"}],
                "rejected": [{"type": "pie", "reason": "goal progress is not a composition"}],
            }
        if ranking:
            return {
                "recommendedType": "horizontal_bar",
                "confidence": 0.82,
                "reasons": ["category cardinality above 4"],
                "alternatives": [{"type": "table_view", "reason": "exact values"}],
                "rejected": [{"type": "pie", "reason": "too many categories"}],
            }
        if composition:
            return {
                "recommendedType": "doughnut",
                "confidence": 0.7,
                "reasons": ["low-cardinality composition candidate"],
                "alternatives": [{"type": "bar", "reason": "safer comparison"}],
                "rejected": [],
            }
        alternatives.append({"type": "kpi_view", "reason": "single snapshot"})
        return {
            "recommendedType": "bar",
            "confidence": 0.55,
            "reasons": ["default category comparison"],
            "alternatives": alternatives,
            "rejected": [],
        }

    @classmethod
    def design_audit(cls, native_config: Mapping[str, Any] | None) -> dict[str, Any]:
        raw_issues = SlideLayoutQualityService.collect_native_layout_issues(native_config)
        issues = [_enrich_issue(code) for code in raw_issues]
        return {
            "issues": issues,
            "signals": {"issueCount": len(issues)},
            "layout": {"issueCodes": raw_issues},
        }

    @classmethod
    def visual_recommendation(
        cls,
        digest: Mapping[str, Any],
        *,
        dominant_visual_family: str | None = None,
    ) -> dict[str, Any]:
        rec = cls._recommend(digest)
        family = str(dominant_visual_family or "").strip()
        if not family:
            return rec
        rejected = {
            str(item.get("type") or "")
            for item in rec.get("rejected") or []
            if isinstance(item, dict)
        }
        alternatives = [
            item
            for item in rec.get("alternatives") or []
            if isinstance(item, dict)
            and str(item.get("type") or "") not in rejected
            and str(item.get("type") or "") != family
        ]
        reasons = list(rec.get("reasons") or [])
        recommended = str(rec.get("recommendedType") or "")
        if recommended == family and alternatives:
            recommended = str(alternatives[0].get("type") or recommended)
            reasons.append("dominant visual family is repetitive")
        elif recommended == family:
            reasons.append("no compatible alternative for the repetitive family")
        return {
            **rec,
            "recommendedType": recommended,
            "reasons": reasons,
            "alternatives": alternatives,
        }


_ISSUE_PROFILES: dict[str, dict[str, Any]] = {
    "kpi_density_exceeded": {
        "category": "density",
        "message": "Há indicadores demais para um único slide.",
        "recommendation": "Distribua os KPIs em outra tela ou use a grade de quatro.",
        "recommendedRecipe": "TV_KPI_GRID_4",
        "safeAutoFix": False,
    },
    "block_overlap": {
        "category": "layout",
        "message": "Blocos se sobrepõem acima do limite do layout.",
        "recommendation": "Reposicione os blocos nos slots da recipe.",
        "safeAutoFix": True,
    },
    "block_frame_overflow": {
        "category": "layout",
        "message": "O frame do bloco sai da área do slide.",
        "recommendation": "Traga o frame para dentro da safe area.",
        "safeAutoFix": True,
    },
    "block_frame_non_positive": {
        "category": "layout",
        "message": "O frame do bloco tem largura ou altura inválida.",
        "recommendation": "Defina um frame positivo dentro da safe area.",
        "safeAutoFix": True,
    },
    "safe_area_violation": {
        "category": "layout",
        "message": "O frame invade a margem segura do slide.",
        "recommendation": "Afaste o bloco da borda usando safeMargin.",
        "safeAutoFix": True,
    },
    "widescreen_single_data_visual": {
        "category": "layout",
        "message": "Um único visual de dado ocupa a tela inteira.",
        "recommendation": "Adicione hierarquia (título ou KPI) se o pedido pedir composição.",
        "safeAutoFix": False,
    },
    "low_contrast": {
        "category": "typography",
        "message": "O contraste do texto está abaixo do mínimo da TV.",
        "recommendation": "Use a cor de texto dos design tokens.",
        "safeAutoFix": True,
    },
    "part_font_below_min": {
        "category": "typography",
        "message": "A tipografia da parte está abaixo do mínimo do token.",
        "recommendation": "Eleve fontSize até o mínimo de partChrome.",
        "safeAutoFix": True,
    },
    "hierarchy_inverted": {
        "category": "typography",
        "message": "A hierarquia tipográfica da parte está invertida.",
        "recommendation": "O valor numérico precisa ficar maior que o título.",
        "safeAutoFix": True,
    },
}


def _enrich_issue(code: str) -> dict[str, Any]:
    prefix = code.split(":", 1)[0]
    profile = _ISSUE_PROFILES.get(prefix) or {
        "category": "layout",
        "message": code,
        "recommendation": "Revise o layout no módulo de qualidade do slide.",
        "safeAutoFix": False,
    }
    issue: dict[str, Any] = {
        "id": code,
        "severity": "warning",
        "category": profile["category"],
        "message": profile["message"],
        "blockIds": _block_ids_from_code(code),
        "recommendation": profile["recommendation"],
        "safeAutoFix": bool(profile["safeAutoFix"]),
        "evidence": {"code": code},
    }
    recipe = profile.get("recommendedRecipe")
    if recipe:
        issue["recommendedRecipe"] = recipe
    return issue


def _block_ids_from_code(code: str) -> list[str]:
    parts = code.split(":")
    if len(parts) < 2:
        return []
    prefix = parts[0]
    if prefix == "block_overlap":
        return [item for item in parts[1].split("~") if item]
    if prefix in {
        "block_frame_overflow",
        "block_frame_non_positive",
        "safe_area_violation",
        "low_contrast",
        "part_font_below_min",
        "hierarchy_inverted",
    }:
        return [parts[1]] if parts[1] else []
    return []


def _role_for(name: str, sample: Any) -> str:
    key = name.lower()
    if key in _TEMPORAL_KEYS or key.endswith("_date"):
        return "temporal"
    if any(hint in key for hint in _GOAL_HINTS):
        return "goal"
    if isinstance(sample, (int, float)) and not isinstance(sample, bool):
        return "metric"
    if key in _LABEL_KEYS:
        return "temporal" if key in _TEMPORAL_KEYS else "category"
    return "dimension"


def _unit_for(name: str, sample: Any) -> str | None:
    key = name.lower()
    if any(hint in key for hint in _PERCENT_HINTS):
        return "percent"
    if any(hint in key for hint in _CURRENCY_HINTS):
        return "currency"
    if isinstance(sample, int) and not isinstance(sample, bool):
        return "integer"
    if isinstance(sample, float):
        return "number"
    return None


def _data_type(sample: Any) -> str:
    if isinstance(sample, bool):
        return "boolean"
    if isinstance(sample, int):
        return "integer"
    if isinstance(sample, float):
        return "number"
    return "string"
