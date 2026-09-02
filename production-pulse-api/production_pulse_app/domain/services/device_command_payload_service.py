from __future__ import annotations

from typing import Any

from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    counter_set_max,
    counter_set_min,
)


def normalize_set_command_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Extrai e valida o valor absoluto do contador para o comando ``set``."""
    if not isinstance(payload, dict) or not payload:
        raise DeviceValidationError("set_value_required")

    raw = payload.get("counter")
    if raw is None:
        raw = payload.get("contador")
    if raw is None:
        raw = payload.get("value")
    if raw is None:
        raise DeviceValidationError("set_value_required")

    try:
        if isinstance(raw, bool):
            raise TypeError("bool is not a counter value")
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise DeviceValidationError("set_value_invalid") from exc

    minimum = counter_set_min()
    maximum = counter_set_max()
    if value < minimum or value > maximum:
        raise DeviceValidationError(
            "set_value_out_of_range",
            min=minimum,
            max=maximum,
        )

    return {"counter": value}


__all__ = ["normalize_set_command_payload"]
