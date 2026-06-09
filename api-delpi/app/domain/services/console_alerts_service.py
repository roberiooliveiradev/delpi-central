"""Alertas do console API DELPI — smoke, p95 e SQL lento (Fase 5)."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.domain.services.caller_request_stats_service import (
    get_caller_duration_percentile,
    get_caller_stats_summary,
)
from app.domain.services.observability_snapshot_service import build_observability_snapshot
from app.domain.services.sql_query_telemetry_service import get_sql_health_summary

logger = logging.getLogger(__name__)

_MAX_ALERT_HISTORY = 100
_WEBHOOK_DEBOUNCE_SECONDS = 300

_lock = threading.Lock()
_alert_history: deque[dict[str, Any]] = deque(maxlen=_MAX_ALERT_HISTORY)
_last_webhook_by_code: dict[str, float] = {}


@dataclass(frozen=True)
class ConsoleAlert:
    code: str
    severity: str
    message: str
    details: dict[str, Any]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _p95_threshold_ms() -> float:
    return float(settings.CONSOLE_ALERT_P95_THRESHOLD_MS or 3000)


def _slow_sql_threshold_ms() -> float:
    return float(settings.CONSOLE_ALERT_SLOW_SQL_THRESHOLD_MS or 2500)


def _webhook_enabled() -> bool:
    return bool((settings.CONSOLE_ALERT_WEBHOOK_URL or "").strip())


def evaluate_console_alerts(
    *,
    smoke_result: dict[str, Any] | None = None,
) -> list[ConsoleAlert]:
    alerts: list[ConsoleAlert] = []

    if smoke_result:
        failed = int(smoke_result.get("failed") or 0)
        if failed > 0:
            alerts.append(
                ConsoleAlert(
                    code="smoke_failure",
                    severity="critical",
                    message=f"Smoke suite falhou: {failed} caso(s).",
                    details={
                        "suite_id": smoke_result.get("suiteId"),
                        "passed": smoke_result.get("passed"),
                        "failed": failed,
                        "cases": [
                            {
                                "caseId": item.get("caseId"),
                                "label": item.get("label"),
                                "message": item.get("message"),
                                "status": item.get("status"),
                            }
                            for item in smoke_result.get("cases") or []
                            if not item.get("ok")
                        ],
                    },
                )
            )

    p95_ms = get_caller_duration_percentile(0.95)
    p95_limit = _p95_threshold_ms()
    if p95_ms > p95_limit:
        alerts.append(
            ConsoleAlert(
                code="p95_latency",
                severity="warning",
                message=f"p95 de latência ({p95_ms} ms) acima do limiar ({p95_limit} ms).",
                details={"p95_ms": p95_ms, "threshold_ms": p95_limit},
            )
        )

    sql_health = get_sql_health_summary(limit=10)
    for row in sql_health.get("top_by_duration") or []:
        max_ms = float(row.get("max_ms") or 0)
        if max_ms >= _slow_sql_threshold_ms():
            alerts.append(
                ConsoleAlert(
                    code="slow_sql",
                    severity="warning",
                    message=f"Query lenta detectada ({max_ms} ms).",
                    details={
                        "query_hash": row.get("query_hash"),
                        "preview": row.get("preview"),
                        "max_ms": max_ms,
                        "operation_id": row.get("last_operation_id"),
                        "threshold_ms": _slow_sql_threshold_ms(),
                    },
                )
            )
            break

    return alerts


def _should_send_webhook(code: str) -> bool:
    now = time.monotonic()
    with _lock:
        last_sent = _last_webhook_by_code.get(code)
        if last_sent is not None and now - last_sent < _WEBHOOK_DEBOUNCE_SECONDS:
            return False
        _last_webhook_by_code[code] = now
        return True


def _send_webhook_sync(alerts: list[ConsoleAlert]) -> None:
    url = (settings.CONSOLE_ALERT_WEBHOOK_URL or "").strip()
    if not url:
        return

    payload = {
        "source": "api-delpi-console",
        "evaluated_at": _now_iso(),
        "alerts": [asdict(alert) for alert in alerts],
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(url, json=payload)
        if response.status_code >= 400:
            logger.warning(
                "console_alert_webhook_rejected status=%s",
                response.status_code,
            )
    except Exception:
        logger.warning("console_alert_webhook_failed", exc_info=True)


def store_and_notify_alerts(alerts: list[ConsoleAlert], *, notify: bool = True) -> list[dict[str, Any]]:
    stored: list[dict[str, Any]] = []
    to_notify: list[ConsoleAlert] = []

    for alert in alerts:
        entry = {
            **asdict(alert),
            "recorded_at": _now_iso(),
            "notified": False,
        }
        with _lock:
            _alert_history.appendleft(entry)
        stored.append(entry)

        if notify and _webhook_enabled() and _should_send_webhook(alert.code):
            to_notify.append(alert)
            entry["notified"] = True

    if to_notify:
        threading.Thread(
            target=_send_webhook_sync,
            args=(to_notify,),
            daemon=True,
            name="console-alert-webhook",
        ).start()

    return stored


def process_console_alerts(
    *,
    smoke_result: dict[str, Any] | None = None,
    notify: bool = True,
) -> dict[str, Any]:
    alerts = evaluate_console_alerts(smoke_result=smoke_result)
    stored = store_and_notify_alerts(alerts, notify=notify and settings.CONSOLE_ALERT_WEBHOOK_ENABLED)
    return {
        "evaluated_at": _now_iso(),
        "alert_count": len(alerts),
        "alerts": [asdict(alert) for alert in alerts],
        "stored": stored,
        "webhook_enabled": _webhook_enabled(),
        "webhook_sent": any(item.get("notified") for item in stored),
    }


def build_console_health_summary() -> dict[str, Any]:
    snapshot = build_observability_snapshot(limit=15)
    caller_stats = get_caller_stats_summary(limit=10)
    current_alerts = evaluate_console_alerts()
    recent = list(_alert_history)[:10]

    return {
        "captured_at": _now_iso(),
        "status": "critical"
        if any(alert.severity == "critical" for alert in current_alerts)
        else "warning"
        if current_alerts
        else "ok",
        "open_alert_count": len(current_alerts),
        "open_alerts": [asdict(alert) for alert in current_alerts],
        "recent_alerts": recent,
        "thresholds": {
            "p95_ms": _p95_threshold_ms(),
            "slow_sql_ms": _slow_sql_threshold_ms(),
        },
        "metrics": {
            "p95_ms": get_caller_duration_percentile(0.95),
            "caller_requests": caller_stats.get("total_requests", 0),
            "sql_samples": snapshot.get("sql_health", {}).get("total_samples", 0),
            "cache_hit_rate_pct": snapshot.get("query_cache", {})
            .get("totals", {})
            .get("hit_rate_pct", 0),
        },
        "webhook_configured": _webhook_enabled(),
        "console_app_id": "api-delpi-console",
    }


def list_console_alert_history(*, limit: int = 25) -> dict[str, Any]:
    with _lock:
        items = list(_alert_history)[:limit]
    return {
        "total": len(items),
        "items": items,
        "webhook_enabled": _webhook_enabled(),
        "thresholds": {
            "p95_ms": _p95_threshold_ms(),
            "slow_sql_ms": _slow_sql_threshold_ms(),
        },
    }


def reset_console_alerts_for_tests() -> None:
    with _lock:
        _alert_history.clear()
        _last_webhook_by_code.clear()
