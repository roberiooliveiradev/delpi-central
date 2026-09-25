from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.domain.services.device_connectivity_status_service import (
    resolve_connectivity_status,
)
from production_pulse_app.domain.services.device_monotonic_counter_continuity_service import (
    counter_epoch_value,
    public_metrics,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_binding_repository import (
    PostgresDeviceBindingRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_operator_placement_repository import (
    PostgresOperatorPlacementRepository,
)

_PULSE_COUNTER_ROLE = "pulse_counter"


def _as_int_counter(metrics: dict[str, Any]) -> int:
    raw = metrics.get("counter")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return 0
    return int(raw)


def device_row_to_integration_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    """Contrato S2S mínimo para o MES (production-control)."""
    last_metrics = row.get("last_metrics") if isinstance(row.get("last_metrics"), dict) else {}
    public = public_metrics(last_metrics)
    has_binding = bool(row.get("placement_key") or row.get("work_center_code"))
    connectivity = resolve_connectivity_status(row, has_binding=has_binding)
    last_seen = row.get("last_seen_at")
    return {
        "deviceId": str(row["id"]),
        "branch": row.get("branch"),
        "name": row.get("name"),
        "roleKey": row.get("role_key"),
        "driverKey": row.get("driver_key"),
        "workCenterCode": row.get("work_center_code"),
        "placementKey": row.get("placement_key"),
        "counter": _as_int_counter(public),
        "counterEpoch": counter_epoch_value(last_metrics),
        "online": bool(connectivity.get("online")),
        "status": connectivity.get("status"),
        "lastSeenAt": last_seen.isoformat() if hasattr(last_seen, "isoformat") else last_seen,
        "pollIntervalMs": int(row.get("poll_interval_ms") or 0) or None,
        "lastError": row.get("last_error"),
    }


class IntegrationDeviceSnapshotService:
    def __init__(
        self,
        *,
        placement_repository: PostgresOperatorPlacementRepository | None = None,
        device_repository: PostgresDeviceRepository | None = None,
        binding_repository: PostgresDeviceBindingRepository | None = None,
    ) -> None:
        self._placements = placement_repository or PostgresOperatorPlacementRepository()
        self._devices = device_repository or PostgresDeviceRepository()
        self._bindings = binding_repository or PostgresDeviceBindingRepository()

    def list_by_work_center(
        self,
        *,
        branch: str,
        work_center: str,
        role_key: str | None = _PULSE_COUNTER_ROLE,
    ) -> dict[str, Any]:
        branch_norm = str(branch or "").strip()
        wc = str(work_center or "").strip()
        if branch_norm not in {"01", "02"}:
            raise ValueError("Filial inválida.")
        if not wc:
            raise ValueError("Centro de trabalho obrigatório.")

        placement_key = f"wc:{branch_norm}:{wc}"
        rows = self._placements.list_bound_devices(
            branch=branch_norm,
            anchor_type="work_center",
            placement_key=placement_key,
        )
        if role_key:
            rows = [row for row in rows if str(row.get("role_key") or "") == role_key]

        items = [device_row_to_integration_snapshot(row) for row in rows]
        return {
            "branch": branch_norm,
            "workCenter": wc,
            "placementKey": placement_key,
            "items": items,
        }

    def get_by_device_id(self, device_id: UUID) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))

        binding = self._bindings.get_active(device_id)
        row = dict(device)
        if binding:
            row["work_center_code"] = binding.get("work_center_code")
            row["placement_key"] = binding.get("placement_key")
            row["anchor_type"] = binding.get("anchor_type")
        else:
            row.setdefault("work_center_code", None)
            row.setdefault("placement_key", None)
        return device_row_to_integration_snapshot(row)
