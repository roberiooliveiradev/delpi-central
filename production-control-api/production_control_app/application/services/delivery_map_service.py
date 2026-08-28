"""Mapa de entrega — snapshot congelado por filial (OPs PA com saldo)."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    filter_operations_for_packages,
    operation_key,
    package_keys_from_orders,
)
from production_control_app.domain.services.delivery_map_pull import normalize_pcp_order_rows
from production_control_app.domain.services.production_order_key import order_belongs_to_package

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


_INTERNAL_SNAPSHOT_FIELDS = ("refreshed_by",)


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

    def _progress_delivery_window(self, *, today: date) -> tuple[str | None, str]:
        """Janela de entrega para progresso do pacote (mãe + intermediários).

        Início aberto: filhas podem ter ``C2_DATPRF`` fora do lookback da mãe.
        Fim = hoje + horizonte (evita puxar programação longínqua irrelevante).
        """
        days_forward = max(1, delivery_map_setting_int("progressHorizonDaysForward", 30))
        end = today + timedelta(days=days_forward)
        return None, end.isoformat()

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

    def build_public(self, *, branch: str, search: str = "") -> dict[str, Any]:
        """Mapa de entrega público: leitura anônima do snapshot, sem puxar o TOTVS."""
        code = self._branch_access.assert_valid_branch(branch)
        row = self._snapshots.get(branch=code)
        if row is None:
            raise SnapshotNotFound(
                "O mapa de entrega desta filial ainda não foi publicado pelo PCP."
            )

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)
        payload = self._present(
            branch=code,
            snapshot_row=row,
            search=search,
            today=today,
            seeded=False,
        )
        return self._strip_public_identity(payload)

    def build_public_progress(
        self,
        *,
        branch: str,
        production_orders: list[str],
    ) -> dict[str, Any]:
        """Progresso vivo anônimo — mesma regra do mapa autenticado, sem RBAC."""
        code = self._branch_access.assert_valid_branch(branch)
        return self._build_progress_for_branch(code, production_orders)

    def snapshot_contains_product(self, *, branch: str, product_code: str) -> bool:
        """Confere se o PA aparece no snapshot congelado da filial — sem puxar o TOTVS."""
        code = self._branch_access.assert_valid_branch(branch)
        wanted = str(product_code or "").strip()
        if not wanted:
            return False
        row = self._snapshots.get(branch=code)
        if row is None:
            raise SnapshotNotFound(
                "O mapa de entrega desta filial ainda não foi publicado pelo PCP."
            )
        payload = _parse_payload_json(row)
        wanted_key = wanted.upper()
        for item in payload.get("orders") or []:
            if not isinstance(item, dict):
                continue
            product = str(item.get("product_code") or "").strip()
            if product.upper() == wanted_key:
                return True
        return False

    @staticmethod
    def _strip_public_identity(payload: dict[str, Any]) -> dict[str, Any]:
        public_payload = dict(payload)
        snapshot = public_payload.get("snapshot")
        if isinstance(snapshot, dict):
            public_payload["snapshot"] = {
                key: value
                for key, value in snapshot.items()
                if key not in _INTERNAL_SNAPSHOT_FIELDS
            }
        return public_payload

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
        return self._build_progress_for_branch(code, production_orders)

    def _build_progress_for_branch(
        self,
        branch: str,
        production_orders: list[str],
    ) -> dict[str, Any]:
        order_to_package = package_keys_from_orders(production_orders)
        if not order_to_package:
            return {
                "branch": branch,
                "items": {},
                "polled_at": today_in_timezone(
                    delivery_map_setting_str("timezone", "America/Sao_Paulo")
                ).isoformat(),
            }

        package_keys = set(order_to_package.values())
        fingerprint = ",".join(sorted(package_keys))
        ttl = max(5, delivery_map_setting_int("progressCacheTtlSeconds", 15))
        cached = get_delivery_map_progress_cache(branch, fingerprint)
        if cached is not None:
            return cached

        timezone = delivery_map_setting_str("timezone", "America/Sao_Paulo")
        today = today_in_timezone(timezone)

        operations = self._fetch_package_operations(
            branch=branch,
            package_keys=package_keys,
            today=today,
        )
        # Status de apontamento já vem no GET machine-load/operations (join HZA).
        # Enrich POST extra só sob flag — dobra a latência sem ganho para a barra.
        if delivery_map_setting_int("progressEnrichLiveStatus", 0):
            operations = self._enrich_operations_live_status(
                branch=branch, operations=operations
            )

        grouped = filter_operations_for_packages(operations, package_keys)
        progress_by_package = {
            key: compute_conjunto_progress(grouped.get(key) or [])
            for key in package_keys
        }

        items: dict[str, Any] = {}
        for order, package_key in order_to_package.items():
            stats = progress_by_package.get(package_key) or compute_conjunto_progress([])
            items[order] = {
                "conjunto_key": package_key,
                **stats,
            }

        payload = {
            "branch": branch,
            "items": items,
            "polled_at": today.isoformat(),
        }
        put_delivery_map_progress_cache(branch, fingerprint, payload, ttl_seconds=float(ttl))
        return payload

    def _paginate_machine_load_operations(
        self,
        *,
        branch: str,
        production_order: str | None = None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
        include_closed: bool = False,
    ) -> list[dict[str, Any]]:
        page_size = max(1, min(delivery_map_setting_int("pageSize", 200), 200))
        page = 1
        collected: list[dict[str, Any]] = []

        while True:
            try:
                payload = self._gateway.fetch_machine_load_operations(
                    branch=branch,
                    delivery_start=delivery_start,
                    delivery_end=delivery_end,
                    scheduled_start=scheduled_start,
                    scheduled_end=scheduled_end,
                    production_order=production_order,
                    work_center=None,
                    include_closed=include_closed,
                    page=page,
                    page_size=page_size,
                )
            except DelpiGatewayError:
                break

            data = _unwrap_data(payload)
            batch = _dict_items(data)
            collected.extend(batch)

            pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
            total_pages = int(pagination.get("total_pages") or 0)
            is_complete = bool(pagination.get("is_complete"))
            if is_complete or total_pages <= page or len(batch) < page_size:
                break
            page += 1
            if page > 500:
                break

        return collected

    def _fetch_one_package_operations(
        self,
        *,
        branch: str,
        package_key: str,
        delivery_start: str | None,
        delivery_end: str | None,
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        for item in self._paginate_machine_load_operations(
            branch=branch,
            production_order=package_key,
            delivery_start=delivery_start,
            delivery_end=delivery_end,
            include_closed=True,
        ):
            if order_belongs_to_package(item.get("production_order"), package_key):
                collected.append(item)
        return collected

    def _fetch_package_operations(
        self,
        *,
        branch: str,
        package_keys: set[str],
        today: date,
    ) -> list[dict[str, Any]]:
        """Operações SH8 do pacote (mãe + intermediários), por C2_NUM+C2_ITEM (8).

        Prefixo de 8 dígitos — não C2_NUM sozinho (mistura itens distintos).
        Inclui OPs encerradas; início de entrega aberto.
        Pacotes em paralelo (workers configuráveis) — N sequencial era a latência.
        """
        if not package_keys:
            return []

        delivery_start, delivery_end = self._progress_delivery_window(today=today)
        keys = sorted(package_keys)
        workers = max(1, min(delivery_map_setting_int("progressFetchMaxWorkers", 6), len(keys)))
        deduped: dict[tuple[str, str], dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    self._fetch_one_package_operations,
                    branch=branch,
                    package_key=package_key,
                    delivery_start=delivery_start,
                    delivery_end=delivery_end,
                )
                for package_key in keys
            ]
            for future in as_completed(futures):
                for item in future.result():
                    deduped[operation_key(item)] = item

        return list(deduped.values())

    def _enrich_operations_live_status(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enrich HZA só das OPs do progresso — não reutiliza cache da carga máquina."""
        if not operations:
            return operations

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
