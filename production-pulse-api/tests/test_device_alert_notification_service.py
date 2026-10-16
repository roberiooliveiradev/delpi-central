"""Alertas Minha DELPI — offline transition + OTA failed (positive/sibling/negative)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from production_pulse_app.application.services.device_alert_notification_service import (
    DEVICE_OFFLINE_CATEGORY,
    OPERATIONAL_FAILURE_CATEGORY,
    DeviceAlertNotificationService,
)
from production_pulse_app.application.security.production_pulse_permissions import (
    ALERTS_RECEIVE,
    BRANCH_VIEW_PERMISSIONS,
)


class _FakeGateway:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []
        self.fail = False

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.fail:
            raise RuntimeError("boom")
        self.payloads.append(payload)
        return {"success": True}


def _online_device(**extra: Any) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    row = {
        "id": uuid4(),
        "name": "ESP32_Lab",
        "branch": "01",
        "ip_address": "192.168.20.6/32",
        "enabled": True,
        "poll_interval_ms": 30_000,
        "last_seen_at": now - timedelta(seconds=1),
        "last_poll_attempt_at": now - timedelta(seconds=1),
        "last_error": None,
    }
    row.update(extra)
    return row


def test_offline_transition_dispatches_with_alerts_permission():
    gw = _FakeGateway()
    svc = DeviceAlertNotificationService(gateway=gw)
    device = _online_device()

    svc.notify_device_went_offline(
        device=device,
        previous_status="online",
        next_status="offline",
        error_code="timeout",
    )

    assert len(gw.payloads) == 1
    payload = gw.payloads[0]
    assert payload["category"] == DEVICE_OFFLINE_CATEGORY
    assert payload["permissionCodes"] == [ALERTS_RECEIVE]
    assert payload["requiredPermissionCodes"] == [BRANCH_VIEW_PERMISSIONS["01"]]
    assert payload["sourceApp"] == "production-pulse"
    assert payload["type"] == "warning"
    assert "ESP32_Lab" in payload["message"]


def test_already_offline_does_not_dispatch():
    """Negative: continuous offline does not spam."""
    gw = _FakeGateway()
    svc = DeviceAlertNotificationService(gateway=gw)
    device = _online_device()

    svc.notify_device_went_offline(
        device=device,
        previous_status="offline",
        next_status="offline",
        error_code="timeout",
    )

    assert gw.payloads == []


def test_ota_failed_dispatches_operational_category():
    """Sibling: OTA failure uses operational category."""
    gw = _FakeGateway()
    svc = DeviceAlertNotificationService(gateway=gw)
    device = _online_device(branch="02")
    target = {
        "id": uuid4(),
        "job_id": uuid4(),
        "device_id": device["id"],
        "to_version": "1.2.0.0",
        "error_code": "ota_target_stale",
    }

    svc.notify_ota_target_failed(
        device=device,
        target=target,
        branch="02",
        error_code="ota_target_stale",
    )

    assert len(gw.payloads) == 1
    payload = gw.payloads[0]
    assert payload["category"] == OPERATIONAL_FAILURE_CATEGORY
    assert payload["permissionCodes"] == [ALERTS_RECEIVE]
    assert payload["requiredPermissionCodes"] == [BRANCH_VIEW_PERMISSIONS["02"]]
    assert payload["type"] == "error"


def test_gateway_none_is_noop():
    svc = DeviceAlertNotificationService(gateway=None)
    svc.notify_device_went_offline(
        device=_online_device(),
        previous_status="online",
        next_status="offline",
    )


def test_gateway_failure_does_not_raise():
    gw = _FakeGateway()
    gw.fail = True
    svc = DeviceAlertNotificationService(gateway=gw)
    svc.notify_device_went_offline(
        device=_online_device(),
        previous_status="online",
        next_status="offline",
        error_code="timeout",
    )
