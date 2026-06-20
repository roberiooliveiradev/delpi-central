"""Métricas de assertividade na validação de desenhos — Fase 15.8.6."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ChatDrawingValidationAssertivenessMetricsService:
    _BASELINE_PATH = (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "drawing_assertiveness_baseline.json"
    )

    @classmethod
    def load_baseline(cls, path: Path | None = None) -> dict[str, Any]:
        target = path or cls._BASELINE_PATH

        if not target.is_file():
            return {"samples": {}, "maxFalseCriticalRate": 0.05}

        payload = json.loads(target.read_text(encoding="utf-8"))

        return payload if isinstance(payload, dict) else {"samples": {}}

    @classmethod
    def evaluate_row(
        cls,
        row: dict[str, Any],
        *,
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        code = str(row.get("code") or "").strip()
        baseline = baseline if isinstance(baseline, dict) else cls.load_baseline()
        samples = baseline.get("samples") if isinstance(baseline.get("samples"), dict) else {}
        sample = samples.get(code) if isinstance(samples.get(code), dict) else {}

        critical = int(row.get("criticalErrors") or 0)
        status = str(row.get("validationStatus") or "").strip()
        max_critical = int(sample.get("maxCriticalErrors", 0))
        allowed_statuses = sample.get("allowedStatuses")

        if not isinstance(allowed_statuses, list):
            allowed_statuses = []

        false_critical = critical > max_critical
        status_ok = not allowed_statuses or status in allowed_statuses
        pending_count = len(row.get("pendingItems") or [])
        checklist_count = int(row.get("checklistItems") or 0)
        pending_rate = (
            float(pending_count) / float(checklist_count)
            if checklist_count > 0
            else 0.0
        )

        return {
            "code": code,
            "falseCritical": false_critical,
            "statusOk": status_ok,
            "criticalErrors": critical,
            "maxCriticalErrors": max_critical,
            "validationStatus": status,
            "pendingRate": round(pending_rate, 4),
            "trueCritical": critical > 0 and not false_critical,
        }

    @classmethod
    def aggregate(
        cls,
        rows: list[dict[str, Any]],
        *,
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        baseline = baseline if isinstance(baseline, dict) else cls.load_baseline()
        evaluated = [cls.evaluate_row(row, baseline=baseline) for row in rows if isinstance(row, dict)]
        total = len(evaluated)

        if total == 0:
            return {
                "sampleCount": 0,
                "falseCriticalRate": 0.0,
                "trueCriticalRate": 0.0,
                "pendingRateAvg": 0.0,
                "passesGate": True,
                "samples": [],
            }

        false_count = sum(1 for item in evaluated if item.get("falseCritical"))
        true_count = sum(1 for item in evaluated if item.get("trueCritical"))
        pending_avg = sum(float(item.get("pendingRate") or 0.0) for item in evaluated) / total
        max_rate = float(baseline.get("maxFalseCriticalRate") or 0.05)
        false_rate = false_count / total

        return {
            "sampleCount": total,
            "falseCriticalCount": false_count,
            "trueCriticalCount": true_count,
            "falseCriticalRate": round(false_rate, 4),
            "trueCriticalRate": round(true_count / total, 4),
            "pendingRateAvg": round(pending_avg, 4),
            "maxFalseCriticalRate": max_rate,
            "passesGate": false_rate <= max_rate,
            "samples": evaluated,
        }

    @classmethod
    def assertiveness_gate_passes(
        cls,
        rows: list[dict[str, Any]],
        *,
        baseline: dict[str, Any] | None = None,
    ) -> bool:
        return bool(cls.aggregate(rows, baseline=baseline).get("passesGate"))
