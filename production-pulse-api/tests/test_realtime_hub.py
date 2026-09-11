from __future__ import annotations

import asyncio
from typing import Any

from production_pulse_app.application.services.production_pulse_realtime_hub import (
    ProductionPulseRealtimeHub,
)
from production_pulse_app.application.services.production_pulse_realtime_notify import (
    branch_room,
    notify_device_updated,
    notify_ota_target_updated,
)


class _FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[Any] = []

    async def send_json(self, payload: Any) -> None:
        self.sent.append(payload)


def test_broadcast_rooms_dedupes_same_socket():
    hub = ProductionPulseRealtimeHub()
    socket = _FakeWebSocket()

    async def _run() -> None:
        async with hub._lock:
            hub._rooms[branch_room("01")] = {socket}  # type: ignore[arg-type]
            hub._rooms["device:d1"] = {socket}  # type: ignore[arg-type]
            hub._rooms["ota.job:j1"] = {socket}  # type: ignore[arg-type]
        await hub.broadcast_now_rooms(
            [branch_room("01"), "device:d1", "ota.job:j1"],
            {"type": "device.updated", "deviceId": "d1"},
        )

    asyncio.run(_run())
    assert len(socket.sent) == 1
    assert socket.sent[0]["type"] == "device.updated"


def test_notify_ota_target_throttles_same_progress(monkeypatch):
    calls: list[dict[str, Any]] = []

    class _Hub:
        def schedule_broadcast_rooms(self, room_keys, payload):
            calls.append({"rooms": list(room_keys), "payload": payload})

    monkeypatch.setattr(
        "production_pulse_app.application.services.production_pulse_realtime_notify.production_pulse_realtime_hub",
        _Hub(),
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.production_pulse_realtime_notify.settings.PP_REALTIME_ENABLED",
        True,
    )

    kwargs = dict(
        reason="progress",
        target_id="t1",
        job_id="j1",
        device_id="d1",
        branch="01",
        status="downloading",
        progress_percent=10,
    )
    notify_ota_target_updated(**kwargs)
    notify_ota_target_updated(**kwargs)
    assert len(calls) == 1

    notify_ota_target_updated(**{**kwargs, "progress_percent": 20})
    assert len(calls) == 2

    notify_ota_target_updated(**{**kwargs, "status": "applying", "progress_percent": 100, "force": True})
    assert len(calls) == 3


def test_notify_device_respects_disabled_flag(monkeypatch):
    calls: list[Any] = []

    class _Hub:
        def schedule_broadcast_rooms(self, room_keys, payload):
            calls.append(payload)

    monkeypatch.setattr(
        "production_pulse_app.application.services.production_pulse_realtime_notify.production_pulse_realtime_hub",
        _Hub(),
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.production_pulse_realtime_notify.settings.PP_REALTIME_ENABLED",
        False,
    )
    notify_device_updated(reason="patch", device_id="d1", branch="01")
    assert calls == []
