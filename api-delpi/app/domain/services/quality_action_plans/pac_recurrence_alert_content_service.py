from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "pac_recurrence_alerts.json"


class PacRecurrenceAlertContentService:
    @classmethod
    @lru_cache(maxsize=1)
    def bundle(cls) -> dict[str, Any]:
        payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("pac_recurrence_alerts.json inválido")
        return payload

    @classmethod
    def opening_assessment(cls) -> dict[str, Any]:
        section = cls.bundle().get("openingAssessment") or {}
        if not isinstance(section, dict):
            return {}
        return section

    @classmethod
    def window_months(cls) -> int:
        return int(cls.opening_assessment().get("windowMonths") or 12)

    @classmethod
    def score_weights(cls) -> dict[str, float]:
        raw = cls.opening_assessment().get("scoreWeights") or {}
        return {
            "plansInWindow": float(raw.get("plansInWindow", 0.45)),
            "openPlans": float(raw.get("openPlans", 0.35)),
            "totalPlansCap": float(raw.get("totalPlansCap", 0.2)),
        }

    @classmethod
    def thresholds(cls) -> dict[str, float | int]:
        raw = cls.opening_assessment().get("thresholds") or {}
        return {
            "highMinScore": float(raw.get("highMinScore", 0.75)),
            "mediumMinScore": float(raw.get("mediumMinScore", 0.45)),
            "highMinPlansInWindow": int(raw.get("highMinPlansInWindow", 3)),
            "mediumMinPlansInWindow": int(raw.get("mediumMinPlansInWindow", 2)),
        }

    @classmethod
    def total_plans_normalizer(cls) -> int:
        return int(cls.opening_assessment().get("totalPlansNormalizer") or 6)
