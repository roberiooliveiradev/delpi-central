from __future__ import annotations

from typing import Any

from production_pulse_app.domain.errors import DeviceDriverError


def resolve_device_ip(device: dict[str, Any]) -> str:
    raw = device.get("ip_address") or device.get("ipAddress") or ""
    ip = str(raw).strip()
    if not ip:
        raise DeviceDriverError("Device sem ip_address.", code="missing_ip")
    return ip


def device_base_url(device: dict[str, Any]) -> str:
    return f"http://{resolve_device_ip(device)}"


def parse_counter_response(body: Any) -> int:
    if not isinstance(body, dict):
        raise DeviceDriverError("Resposta inválida do dispositivo.", code="invalid_response")

    raw = body.get("contador")
    if raw is None:
        raw = body.get("counter")

    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DeviceDriverError(
            "Resposta do dispositivo não contém contador inteiro.",
            code="invalid_response",
        ) from exc
