from __future__ import annotations

from typing import Any

import httpx

from production_pulse_app.domain.errors import DeviceDriverError

_DEVICE_TOKEN_HEADER = "X-Device-Token"


def resolve_device_ip(device: dict[str, Any]) -> str:
    raw = device.get("ip_address") or device.get("ipAddress") or ""
    ip = str(raw).strip()
    if not ip:
        raise DeviceDriverError("missing_ip")
    return ip


def device_base_url(device: dict[str, Any]) -> str:
    return f"http://{resolve_device_ip(device)}"


def resolve_device_api_token(device: dict[str, Any]) -> str | None:
    raw = device.get("device_api_token")
    if raw is None:
        raw = device.get("apiToken")
    if raw is None:
        return None
    token = str(raw).strip()
    return token or None


def device_auth_headers(device: dict[str, Any]) -> dict[str, str]:
    token = resolve_device_api_token(device)
    if not token:
        return {}
    return {_DEVICE_TOKEN_HEADER: token}


def request_device_json(
    *,
    client: httpx.Client | None,
    method: str,
    url: str,
    timeout_seconds: float,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    normalized_method = (method or "GET").strip().upper()
    request_headers = dict(headers or {})
    try:
        if client is not None:
            if normalized_method == "GET":
                response = client.get(url, timeout=timeout_seconds, headers=request_headers)
            else:
                response = client.post(
                    url,
                    json=json_body or {},
                    timeout=timeout_seconds,
                    headers=request_headers,
                )
        else:
            with httpx.Client(timeout=timeout_seconds) as ephemeral:
                if normalized_method == "GET":
                    response = ephemeral.get(url, headers=request_headers)
                else:
                    response = ephemeral.post(
                        url,
                        json=json_body or {},
                        headers=request_headers,
                    )
    except httpx.TimeoutException as exc:
        raise DeviceDriverError(
            "timeout",
            technical_detail=f"HTTP timeout for {url}",
        ) from exc
    except httpx.RequestError as exc:
        raise DeviceDriverError(
            "network_error",
            technical_detail=f"HTTP request failed for {url}: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise DeviceDriverError(
            "http_error",
            technical_detail=f"HTTP {response.status_code} from {url}",
            http_status=response.status_code,
        )

    try:
        return response.json()
    except ValueError as exc:
        raise DeviceDriverError(
            "invalid_response",
            technical_detail=f"Invalid JSON from {url}",
        ) from exc


def device_get_json(
    device: dict[str, Any],
    path: str,
    *,
    client: httpx.Client | None,
    timeout_seconds: float,
) -> Any:
    url = f"{device_base_url(device)}{path}"
    return request_device_json(
        client=client,
        method="GET",
        url=url,
        timeout_seconds=timeout_seconds,
        headers=device_auth_headers(device),
    )


def device_post_json(
    device: dict[str, Any],
    path: str,
    *,
    client: httpx.Client | None,
    timeout_seconds: float,
    payload: dict[str, Any] | None = None,
) -> Any:
    url = f"{device_base_url(device)}{path}"
    return request_device_json(
        client=client,
        method="POST",
        url=url,
        timeout_seconds=timeout_seconds,
        json_body=payload,
        headers=device_auth_headers(device),
    )


def parse_counter_response(body: Any) -> int:
    if not isinstance(body, dict):
        raise DeviceDriverError(
            "invalid_response",
            technical_detail="Response body is not a JSON object.",
        )

    raw = body.get("contador")
    if raw is None:
        raw = body.get("counter")

    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DeviceDriverError(
            "invalid_response",
            technical_detail="Response has no integer counter field.",
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
        raise DeviceDriverError(
            "invalid_response",
            technical_detail="Response body is not a JSON object.",
        )

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
            "invalid_response",
            technical_detail="Response has no numeric rpm or temperature field.",
        )

    return metrics


def parse_device_config_response(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    payload: dict[str, Any] = {}
    ssid = body.get("ssid")
    if ssid is not None and str(ssid).strip():
        payload["ssid"] = str(ssid).strip()
    if "debounceMs" in body:
        try:
            payload["debounceMs"] = int(body.get("debounceMs"))
        except (TypeError, ValueError):
            pass
    if "passwordSet" in body:
        payload["passwordSet"] = bool(body.get("passwordSet"))
    if "apiTokenSet" in body:
        payload["apiTokenSet"] = bool(body.get("apiTokenSet"))
    if "wifiConfigured" in body:
        payload["wifiConfigured"] = bool(body.get("wifiConfigured"))
    return payload
