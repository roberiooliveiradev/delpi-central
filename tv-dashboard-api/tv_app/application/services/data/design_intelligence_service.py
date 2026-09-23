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
    def visual_recommendation(cls, digest: Mapping[str, Any]) -> dict[str, Any]:
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
        issues: list[dict[str, Any]] = []
        for code in raw_issues:
            severity = "warning"
            category = "layout"
            safe = False
            if code.startswith("kpi_density") or "primary" in code:
                category = "density"
                safe = False
            elif "overlap" in code:
                category = "layout"
                safe = True
            elif "contrast" in code or "font" in code:
                category = "typography"
                safe = True
            issues.append(
                {
                    "id": code,
                    "severity": severity,
                    "category": category,
                    "message": code,
                    "safeAutoFix": safe,
                    "evidence": {"code": code},
                }
            )
        return {
            "issues": issues,
            "signals": {"issueCount": len(issues)},
            "layout": {"issueCodes": raw_issues},
        }


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
