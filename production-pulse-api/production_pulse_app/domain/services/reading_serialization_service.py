from __future__ import annotations

from typing import Any


def reading_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "deviceId": str(row["device_id"]),
        "metrics": row.get("metrics") or {},
        "deltaMetrics": row.get("delta_metrics") or {},
        "meta": row.get("meta") or {},
        "source": row["source"],
        "recordedAt": row.get("recorded_at"),
        "createdAt": row.get("created_at"),
    }
