from __future__ import annotations

import json
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from production_control_app.core.security import PC_MACHINE_LOAD_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError, SnapshotNotFound
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.current_month_period import (
    forward_window_bounds,
    today_in_timezone,
)

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "machine_load.json"
_SNAPSHOT_SCHEMA_VERSION = 1

_STATUS_FIELDS = (
    "production_status",
    "is_in_production",
    "production_started_date",
    "production_started_time",
    "active_operator_code",
    "active_operator_name",
    "active_operator_count",
    "appointment_count",
    "last_appointment_date",
)


@lru_cache(maxsize=1)
def _machine_load_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data
    return payload if isinstance(payload, dict) else {}


def _parse_iso_date(value: str | None) -> date | None:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _dict_items(payload: dict[str, Any] | list[Any] | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _user_label(user: object | None) -> str | None:
    if user is None:
        return None
    for attr in ("id", "username", "email", "preferred_username"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:120]
    return None


def _operation_key(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("production_order") or "").strip(),
        str(item.get("operation_code") or "").strip(),
    )


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


class MachineLoadService:
    """Snapshot congelado da fila + status HZA vivo a cada leitura."""

    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        snapshots: MachineLoadSnapshotRepositoryPort,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._snapshots = snapshots
        self._branch_access = branch_access or BranchAccessService()

    def resolve_window(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        today: date | None = None,
    ) -> tuple[date, date]:
        cfg = _machine_load_settings()
        timezone = str(cfg.get("timezone") or "America/Sao_Paulo")
        window_days = _as_int(cfg.get("defaultWindowDays"), 7)
        max_days = _as_int(cfg.get("maxWindowDays"), 90)

        reference = today or today_in_timezone(timezone)
        parsed_start = _parse_iso_date(start_date)
        parsed_end = _parse_iso_date(end_date)

        if parsed_start is None and parsed_end is None:
            return forward_window_bounds(
                timezone=timezone, days=window_days, today=reference
            )

        default_start, default_end = forward_window_bounds(
            timezone=timezone, days=window_days, today=reference
        )
        start = parsed_start or default_start
        end = parsed_end or default_end
        if start > end:
            raise ValueError("A data inicial não pode ser posterior à data final.")
        if (end - start).days + 1 > max_days:
            raise ValueError(f"Período máximo permitido: {max_days} dias.")
        return start, end

    def build(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        self._assert_can_view(user, branch)
        start, end = self.resolve_window(start_date=start_date, end_date=end_date)
        row = self._snapshots.get(branch=branch, start_date=start, end_date=end)
        seeded = False
        if row is None:
            row = self._pull_and_store(
                user,
                branch=branch,
                start=start,
                end=end,
            )
            seeded = True
        return self._present(
            row,
            work_center=work_center,
            seeded=seeded,
            branch=branch,
        )

    def refresh(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        self._assert_can_view(user, branch)
        start, end = self.resolve_window(start_date=start_date, end_date=end_date)
        row = self._pull_and_store(user, branch=branch, start=start, end=end)
        return self._present(
            row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )

    def reorder_sequence(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str,
        ordered_keys: list[dict[str, Any]],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Reordena as operações de um CT no snapshot sem puxar o TOTVS."""
        self._assert_can_view(user, branch)
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("workCenter é obrigatório para reordenar a sequência.")

        start, end = self.resolve_window(start_date=start_date, end_date=end_date)
        row = self._snapshots.get(branch=branch, start_date=start, end_date=end)
        if row is None:
            raise SnapshotNotFound(
                "Não há carga máquina congelada para este período. Atualize a partir do TOTVS."
            )

        payload = self._decode_payload(row)
        operations = _dict_items(payload.get("operations"))
        if not operations and isinstance(payload.get("operations"), list):
            operations = _dict_items(payload["operations"])

        reordered = self._apply_center_order(
            operations,
            work_center=center,
            ordered_keys=ordered_keys,
        )
        now = datetime.now(timezone.utc).isoformat()
        payload["operations"] = reordered
        payload["sequence_updated_at"] = now
        payload["sequence_updated_by"] = _user_label(user)

        updated = self._snapshots.update_payload(
            branch=branch,
            start_date=start,
            end_date=end,
            payload=payload,
        )
        return self._present(
            updated,
            work_center=center,
            seeded=False,
            branch=branch,
        )

    @staticmethod
    def _decode_payload(row: dict[str, Any]) -> dict[str, Any]:
        raw_payload = row.get("payload_json")
        if isinstance(raw_payload, str):
            payload = json.loads(raw_payload)
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = {}
        return dict(payload)

    @staticmethod
    def _apply_center_order(
        operations: list[dict[str, Any]],
        *,
        work_center: str,
        ordered_keys: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        center_ops = [
            item
            for item in operations
            if str(item.get("work_center") or "").strip() == work_center
        ]
        if not center_ops:
            raise ValueError(f"Centro de trabalho '{work_center}' sem operações neste snapshot.")

        by_key = {_operation_key(item): item for item in center_ops}
        if len(by_key) != len(center_ops):
            raise ValueError(
                "Há operações duplicadas (OP + operação) neste centro; não é possível reordenar."
            )

        requested: list[tuple[str, str]] = []
        for raw in ordered_keys:
            key = (
                str(raw.get("production_order") or "").strip(),
                str(raw.get("operation_code") or "").strip(),
            )
            if not key[0] or not key[1]:
                raise ValueError("Cada item de ordered_keys precisa de production_order e operation_code.")
            requested.append(key)

        if len(requested) != len(set(requested)):
            raise ValueError("ordered_keys contém chaves duplicadas.")
        expected = set(by_key.keys())
        if set(requested) != expected:
            raise ValueError(
                "ordered_keys deve ser a permutação exata das operações deste centro de trabalho."
            )

        slots = [
            index
            for index, item in enumerate(operations)
            if str(item.get("work_center") or "").strip() == work_center
        ]
        next_ops = list(operations)
        for slot, key in zip(slots, requested, strict=True):
            next_ops[slot] = by_key[key]
        return next_ops

    def _assert_can_view(self, user: object | None, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MACHINE_LOAD_VIEW):
            raise PermissionError("Você não tem permissão para ver a carga máquina.")

    def _pull_and_store(
        self,
        user: object | None,
        *,
        branch: str,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        frozen = self._fetch_frozen_payload(branch=branch, start=start, end=end)
        return self._snapshots.upsert(
            branch=branch,
            start_date=start,
            end_date=end,
            payload=frozen,
            refreshed_by=_user_label(user),
            schema_version=_SNAPSHOT_SCHEMA_VERSION,
        )

    def _fetch_frozen_payload(
        self,
        *,
        branch: str,
        start: date,
        end: date,
    ) -> dict[str, Any]:
        cfg = _machine_load_settings()
        page_size = _as_int(cfg.get("operationsPageSize"), 300)
        start_s = start.isoformat()
        end_s = end.isoformat()

        try:
            centers_payload = _unwrap_data(
                self._gateway.fetch_machine_load_work_centers(
                    branch=branch,
                    scheduled_start=start_s,
                    scheduled_end=end_s,
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível carregar os centros de trabalho."
            ) from exc

        work_centers = _dict_items(centers_payload)
        operations = self._fetch_all_operations(
            branch=branch,
            scheduled_start=start_s,
            scheduled_end=end_s,
            page_size=page_size,
        )
        summary = centers_payload.get("summary")
        summary_dict = summary if isinstance(summary, dict) else {}

        return {
            "work_centers": work_centers,
            "operations": operations,
            "summary": {
                "work_center_count": len(work_centers),
                "operation_count": _as_int(
                    summary_dict.get("operation_count"), len(operations)
                ),
                "order_count": _as_int(summary_dict.get("order_count"), 0),
            },
        }

    def _fetch_all_operations(
        self,
        *,
        branch: str,
        scheduled_start: str,
        scheduled_end: str,
        page_size: int,
    ) -> list[dict[str, Any]]:
        page = 1
        collected: list[dict[str, Any]] = []
        total: int | None = None
        while True:
            try:
                payload = _unwrap_data(
                    self._gateway.fetch_machine_load_operations(
                        branch=branch,
                        scheduled_start=scheduled_start,
                        scheduled_end=scheduled_end,
                        work_center=None,
                        page=page,
                        page_size=page_size,
                    )
                )
            except DelpiGatewayError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise DelpiGatewayError(
                    "Não foi possível carregar a fila do centro de trabalho."
                ) from exc

            batch = _dict_items(payload)
            collected.extend(batch)
            pagination = payload.get("pagination")
            if isinstance(pagination, dict):
                total = _as_int(pagination.get("total"), total or 0)
                if pagination.get("is_complete") is True:
                    break
            if not batch:
                break
            if total is not None and len(collected) >= total:
                break
            if len(batch) < page_size:
                break
            page += 1
            if page > 50:
                break
        return collected

    def _present(
        self,
        row: dict[str, Any],
        *,
        work_center: str | None,
        seeded: bool,
        branch: str,
    ) -> dict[str, Any]:
        raw_payload = row.get("payload_json")
        if isinstance(raw_payload, str):
            payload = json.loads(raw_payload)
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = {}

        work_centers = _dict_items(payload.get("work_centers"))
        if not work_centers and isinstance(payload.get("work_centers"), list):
            work_centers = _dict_items(payload["work_centers"])
        operations = _dict_items(payload.get("operations"))
        if not operations and isinstance(payload.get("operations"), list):
            operations = _dict_items(payload["operations"])

        operations = self._enrich_live_status(branch=branch, operations=operations)
        work_centers = self._recompute_center_counts(work_centers, operations)

        available = [str(item.get("work_center") or "").strip() for item in work_centers]
        requested = str(work_center or "").strip()
        selected_center = (
            requested if requested in available else (available[0] if available else None)
        )
        selected_items = [
            item
            for item in operations
            if selected_center and str(item.get("work_center") or "").strip() == selected_center
        ]

        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        in_production = sum(1 for item in operations if item.get("is_in_production"))

        return {
            "branch": branch,
            "period": {
                "start_date": row["start_date"].isoformat()
                if hasattr(row["start_date"], "isoformat")
                else str(row["start_date"]),
                "end_date": row["end_date"].isoformat()
                if hasattr(row["end_date"], "isoformat")
                else str(row["end_date"]),
            },
            "summary": {
                "work_center_count": len(work_centers),
                "operation_count": _as_int(
                    summary.get("operation_count"), len(operations)
                ),
                "order_count": _as_int(summary.get("order_count"), 0),
                "in_production_count": in_production,
            },
            "snapshot": {
                "refreshed_at": _iso_timestamp(row.get("refreshed_at")),
                "refreshed_by": row.get("refreshed_by"),
                "seeded": seeded,
                "schema_version": _as_int(row.get("schema_version"), _SNAPSHOT_SCHEMA_VERSION),
                "sequence_updated_at": _iso_timestamp(payload.get("sequence_updated_at")),
                "sequence_updated_by": payload.get("sequence_updated_by"),
            },
            "work_centers": work_centers,
            "selected": {
                "work_center": selected_center,
                "requested_work_center": requested or None,
                "items": selected_items,
                "pagination": {
                    "page": 1,
                    "page_size": len(selected_items),
                    "total": len(selected_items),
                    "is_complete": True,
                },
            },
        }

    def _enrich_live_status(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not operations:
            return operations

        keys = [
            {
                "production_order": order,
                "operation_code": operation,
            }
            for order, operation in {_operation_key(item) for item in operations}
            if order and operation
        ]
        if not keys:
            return operations

        try:
            status_payload = _unwrap_data(
                self._gateway.fetch_machine_load_appointment_status(
                    branch=branch,
                    items=keys,
                )
            )
        except DelpiGatewayError:
            # Snapshot continua útil mesmo se o enrich HZA falhar.
            return operations
        except Exception:
            return operations

        status_by_key = {
            _operation_key(item): item for item in _dict_items(status_payload)
        }
        enriched: list[dict[str, Any]] = []
        for item in operations:
            status = status_by_key.get(_operation_key(item))
            if not status:
                enriched.append(item)
                continue
            merged = dict(item)
            for field in _STATUS_FIELDS:
                if field in status:
                    merged[field] = status[field]
            enriched.append(merged)
        return enriched

    @staticmethod
    def _recompute_center_counts(
        work_centers: list[dict[str, Any]],
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for item in operations:
            center = str(item.get("work_center") or "").strip()
            if center and item.get("is_in_production"):
                counts[center] = counts.get(center, 0) + 1
        updated: list[dict[str, Any]] = []
        for center in work_centers:
            code = str(center.get("work_center") or "").strip()
            next_center = dict(center)
            next_center["in_production_count"] = counts.get(code, 0)
            updated.append(next_center)
        return updated
