"""Conteúdo declarativo dos alertas/SLO do console api-delpi."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "console_alerts.json"


class ConsoleAlertContentService:
    @classmethod
    @lru_cache(maxsize=1)
    def bundle(cls) -> dict[str, Any]:
        payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("console_alerts.json inválido")
        return payload

    @classmethod
    def clear_cache(cls) -> None:
        cls.bundle.cache_clear()

    @classmethod
    def thresholds(cls) -> dict[str, Any]:
        raw = cls.bundle().get("thresholds") or {}
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def pool_saturation_pct_default(cls) -> float:
        return float(cls.thresholds().get("poolSaturationPct") or 90)

    @classmethod
    def slo_targets(cls) -> dict[str, float]:
        raw = cls.bundle().get("slo") or {}
        if not isinstance(raw, dict):
            return {"availability_pct": 99.0, "p95_ms": 3000.0}
        return {
            "availability_pct": float(raw.get("availability_pct") or 99.0),
            "p95_ms": float(raw.get("p95_ms") or 3000),
        }

    @classmethod
    def alert_spec(cls, code: str) -> dict[str, Any]:
        alerts = cls.bundle().get("alerts") or {}
        if not isinstance(alerts, dict):
            return {}
        spec = alerts.get(code) or {}
        return spec if isinstance(spec, dict) else {}

    @classmethod
    def format_alert_message(cls, code: str, **fields: Any) -> str:
        spec = cls.alert_spec(code)
        template = str(spec.get("messageTemplate") or code)
        try:
            return template.format(**fields)
        except (KeyError, ValueError):
            return template

    @classmethod
    def alert_guidance(cls, code: str) -> str:
        return str(cls.alert_spec(code).get("guidance") or "")

    @classmethod
    def alert_severity(cls, code: str, *, default: str = "warning") -> str:
        return str(cls.alert_spec(code).get("severity") or default)

    @classmethod
    def sli_label(cls, key: str) -> str:
        labels = cls.bundle().get("sliLabels") or {}
        if not isinstance(labels, dict):
            return key
        return str(labels.get(key) or key)

    @classmethod
    def empty_traffic_hint(cls) -> str:
        return str(cls.bundle().get("emptyTrafficHint") or "")
