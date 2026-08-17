"""Telemetria mínima do copiloto TV (Onda C) — contadores em memória."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

_lock = threading.Lock()
_events: deque[dict[str, Any]] = deque(maxlen=500)
_counts: dict[str, int] = {
    "preview_ok": 0,
    "preview_rejected": 0,
    "apply_ok": 0,
    "apply_rejected": 0,
    "op_rejected": 0,
}


def record_copilot_event(
    *,
    kind: str,
    ok: bool,
    ops_count: int = 0,
    rejected_op: str | None = None,
    elapsed_ms: float | None = None,
) -> None:
    window = TvCopilotContentService.setting_int("telemetryWindow", 500)
    with _lock:
        if _events.maxlen != window:
            # deque maxlen é imutável — só recria se config mudou em teste
            pass
        key = f"{kind}_{'ok' if ok else 'rejected'}"
        if key in _counts:
            _counts[key] += 1
        if rejected_op:
            _counts["op_rejected"] += 1
        _events.append(
            {
                "ts": time.time(),
                "kind": kind,
                "ok": ok,
                "opsCount": ops_count,
                "rejectedOp": rejected_op,
                "elapsedMs": elapsed_ms,
            }
        )


def copilot_telemetry_snapshot() -> dict[str, Any]:
    with _lock:
        return {
            "counts": dict(_counts),
            "recent": list(_events)[-50:],
        }


def reset_copilot_telemetry() -> None:
    with _lock:
        for key in _counts:
            _counts[key] = 0
        _events.clear()
