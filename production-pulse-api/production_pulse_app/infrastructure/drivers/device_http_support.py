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


def _first_numeric(body: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key not in body:
            continue
        raw = body.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return None


def parse_gauge_response(body: Any) -> dict[str, float]:
    if not isinstance(body, dict):
        raise DeviceDriverError("Resposta inválida do dispositivo.", code="invalid_response")

    rpm = _first_numeric(body, "rpm", "rotacao", "rotação", "rotation")
    temperature_c = _first_numeric(
        body,
        "temperature_c",
        "temperatura",
        "temperatura_c",
        "temp_c",
        "temperature",
    )

    metrics: dict[str, float] = {}
    if rpm is not None:
        metrics["rpm"] = rpm
    if temperature_c is not None:
        metrics["temperature_c"] = temperature_c

    if not metrics:
        raise DeviceDriverError(
            "Resposta do dispositivo não contém rpm ou temperatura numéricos.",
            code="invalid_response",
        )

    return metrics
