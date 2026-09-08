from __future__ import annotations

from typing import Any


def unwrap_delpi_envelope(payload: Any) -> Any:
    """Return `data` from api-delpi `{success,data}` envelope, else payload as-is."""
    if isinstance(payload, dict) and "data" in payload and (
        "success" in payload or "meta" in payload
    ):
        return payload.get("data")
    return payload


def summary_dict(payload: Any) -> dict[str, Any]:
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        return {}
    summary = data.get("summary")
    if isinstance(summary, dict):
        return summary
    return data
