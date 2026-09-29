from __future__ import annotations

from datetime import datetime
from typing import Any


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _seconds(start: Any, end: Any) -> int:
    try:
        delta = (end - start).total_seconds()
    except Exception:  # noqa: BLE001
        return 0
    return max(0, int(delta))


class MesTimelineBuilder:
    def build(
        self,
        *,
        run: dict[str, Any],
        events: list[dict[str, Any]],
        reference_at: datetime,
    ) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        producing_seconds = 0
        stopped_seconds = 0
        stop_count = 0

        ordered_events = sorted(events, key=lambda event: event["started_at"])
        for event in ordered_events:
            started = event["started_at"]
            ended = event.get("ended_at")
            duration = _seconds(started, ended or reference_at)
            downtime = event.get("downtime")

            if event["state"] == "producing":
                producing_seconds += duration
            elif event["state"] == "stopped":
                stopped_seconds += duration
                stop_count += 1

            items.append(
                {
                    "id": event["id"],
                    "state": event["state"],
                    "startedAt": _iso(started),
                    "endedAt": _iso(ended),
                    "durationSeconds": duration,
                    "source": event.get("source"),
                    "downtime": downtime,
                }
            )

        first_started = ordered_events[0]["started_at"] if ordered_events else run.get("started_at")
        run_ended = run.get("ended_at")
        elapsed_seconds = (
            _seconds(first_started, run_ended or reference_at)
            if first_started is not None
            else 0
        )
        return {
            "runId": run["id"],
            "branch": run["branch"],
            "workCenter": run["work_center"],
            "status": run.get("status"),
            "referenceAt": reference_at.isoformat(),
            "summary": {
                "elapsedSeconds": elapsed_seconds,
                "producingSeconds": producing_seconds,
                "stoppedSeconds": stopped_seconds,
                "stopCount": stop_count,
            },
            "items": items,
        }
