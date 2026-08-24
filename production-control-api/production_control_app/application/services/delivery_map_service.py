"""Mapa de entrega — snapshot congelado por filial (OPs PA com saldo)."""

from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from production_control_app.application.services.delivery_map_settings import (
    delivery_map_setting_int,
    delivery_map_setting_str,
)
from production_control_app.application.services.delivery_map_progress_cache import (
    get_delivery_map_progress_cache,
    put_delivery_map_progress_cache,
)
from production_control_app.application.services.machine_load_live_status_cache import (
    get_live_status_cache,
    put_live_status_cache,
)
from production_control_app.core.security import PC_DELIVERY_MAP_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError, SnapshotNotFound
from production_control_app.domain.ports.delivery_map_snapshot_repository import (
    DeliveryMapSnapshotRepositoryPort,
)
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.current_month_period import today_in_timezone
from production_control_app.domain.services.delivery_map_grouping import group_delivery_map_sections
from production_control_app.domain.services.delivery_map_merge import (
    apply_override_updates,
    merge_overrides_after_refresh,
)
from production_control_app.domain.services.conjunto_operation_progress import (
    compute_conjunto_progress,
    conjunto_keys_from_orders,
    filter_operations_for_conjuntos,
    operation_key,
)
from production_control_app.domain.services.delivery_map_pull import normalize_pcp_order_rows

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

_SNAPSHOT_SCHEMA_VERSION = 1
_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "delivery_map.json"


@lru_cache(maxsize=1)
def _settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data
    return payload if isinstance(payload, dict) else {}


def _dict_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
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


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _parse_payload_json(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("payload_json")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {"orders": [], "overrides": {}}


class DeliveryMapService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        snapshots: DeliveryMapSnapshotRepositoryPort,
        *,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._gateway = gateway
        self._snapshots = snapshots
        self._branch_access = branch_access or BranchAccessService()

    def _assert_view(self, user: object | None) -> None:
        if not can(user, PC_DELIVERY_MAP_VIEW):
            raise PermissionError("Você não tem permissão para ver o mapa de entrega.")

    def _delivery_window(self, *, today: date) -> tuple[str, str, date]:
        months_back = max(1, delivery_map_setting_int("includeOverdueMonthsBack", 12))
        days_forward = max(1, delivery_map_setting_int("horizonDaysForward", 30))
        year, month = today.year, today.month - months_back
        while month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1)
        end = today + timedelta(days=days_forward)
        return start.isoformat(), end.isoformat(), end

    def _pull_orders(self, *, branch: str, today: date) -> tuple[list[dict[str, Any]], date]:
        delivery_start, delivery_end, horizon_end = self._delivery_window(today=today)
        page_size = max(1, min(delivery_map_setting_int("pageSize", 200), 200))
        page = 1
        collected: list[dict[str, Any]] = []

        while True:
            payload = self._gateway.fetch_pcp_orders_items_page(
                branch=branch,
                delivery_start=delivery_start,
                delivery_end=delivery_end,
                page=page,
                page_size=page_size,
                sort="delivery_asc",
                mother_only=True,
                open_only=True,
            )
            data = _unwrap_data(payload)
            collected.extend(_dict_items(data))
            pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
            total_pages = int(pagination.get("total_pages") or 0)
            is_complete = bool(pagination.get("is_complete"))
            if is_complete or total_pages <= page or len(_dict_items(data)) < page_size:
                break
            page += 1
            if page > 500:
                break

        return normalize_pcp_order_rows(collected), horizon_end

    def _present(
        self,
        *,
        branch: str,
        snapshot_row: dict[str, Any],
        search: str,
        today: date,
        seeded: bool = False,
    ) -> dict[str, Any]:
        payload = _parse_payload_json(snapshot_row)
        orders = payload.get("orders")
        overrides = payload.get("overrides")
        if not isinstance(orders, list):
            orders = []
        if not isinstance(overrides, dict):
            overrides = {}

        sections = group_delivery_map_sections(
            [item for item in orders if isinstance(item, dict)],
            overrides,
            today=today,
            search=search,
        )
        order_count = sum(section.get("row_count", 0) for section in sections)

        horizon_end = snapshot_row.get("horizon_end")
        horizon_end_s = (
            horizon_end.isoformat()
            if hasattr(horizon_end, "isoformat")
            else str(horizon_end or "")[:10]
            or None
        )

        return {
            "branch": branch,
            "sections": sections,
            "summary": {
                "order_count": order_count,
                "section_count": len(sections),
            },
            "filters": {"search": search.strip()},
            "snapshot": {
                "refreshed_at": _iso_timestamp(snapshot_row.get("refreshed_at")),
                "refreshed_by": snapshot_row.get("refreshed_by"),
                "horizon_end": horizon_end_s,
                "seeded": seeded,
            },
        }

    def _pull_and_store(
        self,
        *,
        branch: str,
        user: object | None,
        previous_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)
        orders, horizon_end = self._pull_orders(branch=branch, today=today)
        order_keys = {str(item["production_order"]) for item in orders}

        prev_overrides = None
        if isinstance(previous_payload, dict):
            prev_overrides = previous_payload.get("overrides")

        payload = {
            "orders": orders,
            "overrides": merge_overrides_after_refresh(
                previous_overrides=prev_overrides,
                order_keys=order_keys,
            ),
        }
        row = self._snapshots.upsert(
            branch=branch,
            horizon_end=horizon_end,
            payload=payload,
            refreshed_by=_user_label(user),
            schema_version=_SNAPSHOT_SCHEMA_VERSION,
        )
        return row

    def build(self, user: object | None, *, branch: str, search: str = "") -> dict[str, Any]:
        self._assert_view(user)
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)

        row = self._snapshots.get(branch=code)
        seeded = False
        if row is None:
            try:
                row = self._pull_and_store(branch=code, user=user)
                seeded = True
            except DelpiGatewayError:
                raise
            except Exception as exc:
                raise DelpiGatewayError("Não foi possível montar o mapa de entrega.") from exc

        return self._present(
            branch=code,
            snapshot_row=row,
            search=search,
            today=today,
            seeded=seeded,
        )

    def refresh(self, user: object | None, *, branch: str, search: str = "") -> dict[str, Any]:
        self._assert_view(user)
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)

        existing = self._snapshots.get(branch=code)
        previous_payload = _parse_payload_json(existing) if existing else None

        try:
            row = self._pull_and_store(
                branch=code,
                user=user,
                previous_payload=previous_payload,
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:
            raise DelpiGatewayError("Não foi possível atualizar o mapa de entrega.") from exc

        return self._present(
            branch=code,
            snapshot_row=row,
            search=search,
            today=today,
            seeded=False,
        )

    def patch_overrides(
        self,
        user: object | None,
        *,
        branch: str,
        updates: list[dict[str, Any]],
        search: str = "",
    ) -> dict[str, Any]:
        self._assert_view(user)
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)

        row = self._snapshots.get(branch=code)
        if row is None:
            raise SnapshotNotFound("Mapa de entrega ainda não foi carregado para esta filial.")

        payload = _parse_payload_json(row)
        overrides = payload.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}

        order_keys = {
            str(item.get("production_order") or "").strip()
            for item in payload.get("orders") or []
            if isinstance(item, dict)
        }

        filtered_updates: list[dict[str, Any]] = []
        for raw in updates:
            if not isinstance(raw, dict):
                continue
            key = str(raw.get("production_order") or "").strip()
            if key and key in order_keys:
                filtered_updates.append(raw)

        payload["overrides"] = apply_override_updates(overrides, filtered_updates)
        updated = self._snapshots.update_payload(branch=code, payload=payload)

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)
        return self._present(
            branch=code,
            snapshot_row=updated,
            search=search,
            today=today,
            seeded=False,
        )

    def build_progress(
        self,
        user: object | None,
        *,
        branch: str,
        production_orders: list[str],
    ) -> dict[str, Any]:
        """Progresso vivo por conjunto — independe do snapshot congelado da lista."""
        self._assert_view(user)
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)

        order_to_conjunto = conjunto_keys_from_orders(production_orders)
        if not order_to_conjunto:
            return {
                "branch": code,
                "items": {},
                "polled_at": today_in_timezone(
                    delivery_map_setting_str("timezone", "America/Sao_Paulo")
                ).isoformat(),
            }

        conjunto_keys = set(order_to_conjunto.values())
        fingerprint = ",".join(sorted(conjunto_keys))
        ttl = max(5, delivery_map_setting_int("progressCacheTtlSeconds", 15))
        cached = get_delivery_map_progress_cache(code, fingerprint)
        if cached is not None:
            return cached

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)
        delivery_start, delivery_end, _ = self._delivery_window(today=today)

        operations = self._fetch_machine_load_operations_window(
            branch=code,
            delivery_start=delivery_start,
            delivery_end=delivery_end,
            conjunto_keys=conjunto_keys,
        )
        operations = self._enrich_operations_live_status(branch=code, operations=operations)

        grouped = filter_operations_for_conjuntos(operations, conjunto_keys)
        progress_by_conjunto = {
            key: compute_conjunto_progress(grouped.get(key) or [])
            for key in conjunto_keys
        }

        items: dict[str, Any] = {}
        for order, conjunto in order_to_conjunto.items():
            stats = progress_by_conjunto.get(conjunto) or compute_conjunto_progress([])
            items[order] = {
                "conjunto_key": conjunto,
                **stats,
            }

        payload = {
            "branch": code,
            "items": items,
            "polled_at": today.isoformat(),
        }
        put_delivery_map_progress_cache(code, fingerprint, payload, ttl_seconds=float(ttl))
        return payload

    def _fetch_machine_load_operations_window(
        self,
        *,
        branch: str,
        delivery_start: str,
        delivery_end: str,
        conjunto_keys: set[str],
    ) -> list[dict[str, Any]]:
        if not conjunto_keys:
            return []

        page_size = max(1, min(delivery_map_setting_int("pageSize", 200), 200))
        page = 1
        collected: list[dict[str, Any]] = []

        while True:
            try:
                payload = self._gateway.fetch_machine_load_operations(
                    branch=branch,
                    delivery_start=delivery_start,
                    delivery_end=delivery_end,
                    work_center=None,
                    page=page,
                    page_size=page_size,
                )
            except DelpiGatewayError:
                break

            data = _unwrap_data(payload)
            batch = _dict_items(data)
            for item in batch:
                order = str(item.get("production_order") or "").strip()
                for key in conjunto_keys:
                    if order.startswith(key):
                        collected.append(item)
                        break

            pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
            total_pages = int(pagination.get("total_pages") or 0)
            is_complete = bool(pagination.get("is_complete"))
            if is_complete or total_pages <= page or len(batch) < page_size:
                break
            page += 1
            if page > 500:
                break

        return collected

    def _enrich_operations_live_status(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not operations:
            return operations

        cached = get_live_status_cache(branch)
        if cached is not None:
            return self._apply_status_map(operations, cached)

        keys = [
            {"production_order": order, "operation_code": operation}
            for order, operation in {operation_key(item) for item in operations}
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
            return operations
        except Exception:
            return operations

        status_by_key = {operation_key(item): item for item in _dict_items(status_payload)}
        put_live_status_cache(branch, status_by_key)
        return self._apply_status_map(operations, status_by_key)

    @staticmethod
    def _apply_status_map(
        operations: list[dict[str, Any]],
        status_by_key: dict[tuple[str, str], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in operations:
            status = status_by_key.get(operation_key(item))
            if not status:
                enriched.append(item)
                continue
            merged = dict(item)
            for field in _STATUS_FIELDS:
                if field in status:
                    merged[field] = status[field]
            enriched.append(merged)
        return enriched

    def build_progress(
        self,
        user: object | None,
        *,
        branch: str,
        production_orders: list[str],
    ) -> dict[str, Any]:
        """Progresso vivo por conjunto — independe do snapshot congelado da lista."""
        self._assert_view(user)
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)

        order_to_conjunto = conjunto_keys_from_orders(production_orders)
        if not order_to_conjunto:
            return {
                "branch": code,
                "items": {},
                "polled_at": today_in_timezone(
                    delivery_map_setting_str("timezone", "America/Sao_Paulo")
                ).isoformat(),
            }

        conjunto_keys = set(order_to_conjunto.values())
        fingerprint = ",".join(sorted(conjunto_keys))
        ttl = max(5, delivery_map_setting_int("progressCacheTtlSeconds", 15))
        cached = get_delivery_map_progress_cache(code, fingerprint)
        if cached is not None:
            return cached

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)
        delivery_start, delivery_end, _ = self._delivery_window(today=today)

        operations = self._fetch_machine_load_operations_window(
            branch=code,
            delivery_start=delivery_start,
            delivery_end=delivery_end,
            conjunto_keys=conjunto_keys,
        )
        operations = self._enrich_operations_live_status(branch=code, operations=operations)

        grouped = filter_operations_for_conjuntos(operations, conjunto_keys)
        progress_by_conjunto = {
            key: compute_conjunto_progress(grouped.get(key) or [])
            for key in conjunto_keys
        }

        items: dict[str, Any] = {}
        for order, conjunto in order_to_conjunto.items():
            stats = progress_by_conjunto.get(conjunto) or compute_conjunto_progress([])
            items[order] = {
                "conjunto_key": conjunto,
                **stats,
            }

        payload = {
            "branch": code,
            "items": items,
            "polled_at": today.isoformat(),
        }
        put_delivery_map_progress_cache(code, fingerprint, payload, ttl_seconds=float(ttl))
        return payload

    def _fetch_machine_load_operations_window(
        self,
        *,
        branch: str,
        delivery_start: str,
        delivery_end: str,
        conjunto_keys: set[str],
    ) -> list[dict[str, Any]]:
        if not conjunto_keys:
            return []

        page_size = max(1, min(delivery_map_setting_int("pageSize", 200), 200))
        page = 1
        collected: list[dict[str, Any]] = []

        while True:
            try:
                payload = self._gateway.fetch_machine_load_operations(
                    branch=branch,
                    delivery_start=delivery_start,
                    delivery_end=delivery_end,
                    work_center=None,
                    page=page,
                    page_size=page_size,
                )
            except DelpiGatewayError:
                break

            data = _unwrap_data(payload)
            batch = _dict_items(data)
            for item in batch:
                order = str(item.get("production_order") or "").strip()
                for key in conjunto_keys:
                    if order.startswith(key):
                        collected.append(item)
                        break

            pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
            total_pages = int(pagination.get("total_pages") or 0)
            is_complete = bool(pagination.get("is_complete"))
            if is_complete or total_pages <= page or len(batch) < page_size:
                break
            page += 1
            if page > 500:
                break

        return collected

    def _enrich_operations_live_status(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not operations:
            return operations

        cached = get_live_status_cache(branch)
        if cached is not None:
            return self._apply_status_map(operations, cached)

        keys = [
            {"production_order": order, "operation_code": operation}
            for order, operation in {operation_key(item) for item in operations}
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
            return operations
        except Exception:
            return operations

        status_by_key = {operation_key(item): item for item in _dict_items(status_payload)}
        put_live_status_cache(branch, status_by_key)
        return self._apply_status_map(operations, status_by_key)

    @staticmethod
    def _apply_status_map(
        operations: list[dict[str, Any]],
        status_by_key: dict[tuple[str, str], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in operations:
            status = status_by_key.get(operation_key(item))
            if not status:
                enriched.append(item)
                continue
            merged = dict(item)
            for field in _STATUS_FIELDS:
                if field in status:
                    merged[field] = status[field]
            enriched.append(merged)
        return enriched
