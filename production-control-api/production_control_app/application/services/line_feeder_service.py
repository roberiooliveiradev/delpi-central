"""Cockpit do Alimentador de Linha.

Orquestra o que já tem dono:

- fila congelada e «está na programação» → snapshot da carga máquina;
- empenho de material → SD4 via api-delpi (lote de OPs);
- saldo por armazém → SB2 via api-delpi (ponto de uso e almoxarifado);
- elegibilidade por horário e rateio do saldo → domain services do alimentador.

A quantidade necessária vem de ``open_qty`` (saldo em aberto do empenho): operação
já apontada não é filtrada aqui porque o próprio Protheus já baixou o empenho.

Nada é escrito no Protheus. A lista de coleta é controle operacional da plataforma.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Sequence
from uuid import UUID

from production_control_app.application.services.line_feeder_settings import (
    message as setting_message,
    setting_int,
    setting_map,
    setting_str,
)
from production_control_app.core.security import PC_LINE_FEEDER_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError, SnapshotNotFound
from production_control_app.domain.ports.line_feeder_pick_plan_repository import (
    LineFeederPickPlanRepositoryPort,
)
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.line_feeder_requirements import (
    MaterialRequirement,
    ProductPickLine,
    build_requirements,
    filter_requirements,
    group_by_work_center,
    normalize_commitments,
    pick_list_by_product,
    pick_list_candidates,
    summarize,
)
from production_control_app.domain.services.line_feeder_schedule_cutoff import (
    filter_by_cutoff,
    parse_cutoff,
)
from production_control_app.domain.services.line_feeder_warehouse_transfers import (
    MOVEMENT_KIND_WAREHOUSE_TRANSFER,
    pair_warehouse_transfers,
)
from production_control_app.domain.services.machine_load_snapshot_payload import (
    decode_snapshot_payload,
    payload_operations,
    payload_work_centers,
)
from production_control_app.domain.services.machine_load_withdrawal import (
    visible_operations,
    withdrawn_order_numbers,
)

logger = logging.getLogger(__name__)

ITEM_STATUSES = ("pending", "picked", "delivered")
PLAN_STATUSES = ("open", "closed")


@dataclass(frozen=True, slots=True)
class _Requirements:
    """Resultado do cálculo global do corte, antes de qualquer recorte de tela."""

    items: tuple[MaterialRequirement, ...]
    work_centers: tuple[dict[str, str], ...]
    operation_count: int
    order_count: int
    balances_available: bool
    truncated_orders: bool
    # product_code -> BZ_MPLOCAL; ausência no mapa = local vazio.
    pickup_locations: dict[str, str]


class _RequirementsCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        self._entries: dict[str, tuple[float, _Requirements]] = {}

    def get(self, key: str) -> _Requirements | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if self._ttl and (time.monotonic() - stored_at) > self._ttl:
            self._entries.pop(key, None)
            return None
        return value

    def set(self, key: str, value: _Requirements) -> None:
        self._entries[key] = (time.monotonic(), value)


_CACHE = _RequirementsCache(setting_int("cacheTtlSeconds", 60))


class LineFeederService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        snapshots: MachineLoadSnapshotRepositoryPort,
        pick_plans: LineFeederPickPlanRepositoryPort,
        branch_access: BranchAccessService | None = None,
        cache: _RequirementsCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._snapshots = snapshots
        self._pick_plans = pick_plans
        self._branch_access = branch_access or BranchAccessService()
        self._cache = cache if cache is not None else _CACHE

    # ------------------------------------------------------------------ #
    # Autorização
    # ------------------------------------------------------------------ #

    def _authorize(self, user: object | None, *, branch: str) -> str:
        code = self._branch_access.assert_valid_branch(branch)
        self._branch_access.assert_can_view_branch(user, code)
        if not can(user, PC_LINE_FEEDER_VIEW):
            raise PermissionError(
                "Você não tem permissão para o cockpit do alimentador de linha."
            )
        return code

    # ------------------------------------------------------------------ #
    # Necessidade por bancada
    # ------------------------------------------------------------------ #

    def get_requirements(
        self,
        user: object | None,
        *,
        branch: str,
        cutoff_date: str | None,
        cutoff_time: str | None,
        work_center: str | None = None,
        status: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        cutoff = self._parse_cutoff(cutoff_date, cutoff_time)
        computed = self._load_requirements(branch=code, cutoff=cutoff, refresh=refresh)

        center = _text(work_center)
        wanted_status = self._normalize_requirement_status(status)
        visible = filter_requirements(
            list(computed.items), work_center=center or None, status=wanted_status
        )
        locations = computed.pickup_locations
        items_payload = [_requirement_payload(item, locations) for item in visible]
        groups = group_by_work_center(visible)
        for group in groups:
            group["items"] = [
                {**row, "pickup_location": locations.get(row.get("product_code") or "", "")}
                for row in group["items"]
            ]

        return {
            "branch": code,
            "cutoff": self._cutoff_payload(cutoff),
            "filters": {
                "work_center": center,
                "status": wanted_status or "",
            },
            "work_centers": [dict(item) for item in computed.work_centers],
            "summary": {
                **summarize(visible),
                "operation_count": computed.operation_count,
                "production_order_count": computed.order_count,
            },
            "groups": groups,
            "items": items_payload,
            "stock": self._stock_payload(computed),
            "statuses": setting_map("statuses"),
            "item_statuses": setting_map("itemStatuses"),
            "didactic": setting_map("didactic"),
        }

    def _stock_payload(self, computed: _Requirements) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "available": computed.balances_available,
            "point_of_use_warehouse": setting_str("pointOfUseWarehouse", "99"),
            "source_warehouse": setting_str("sourceWarehouse", "01"),
        }
        if not computed.balances_available:
            payload["message"] = setting_message(
                "balancesUnavailable",
                "Não foi possível ler o estoque agora.",
            )
        if computed.truncated_orders:
            payload["truncated_orders"] = True
        return payload

    def get_product_detail(
        self,
        user: object | None,
        *,
        product_code: str,
        branch: str,
        cutoff_date: str | None,
        cutoff_time: str | None,
    ) -> dict[str, Any]:
        """Detalhe da MP no corte: identidade, saldo real 01, bancadas e transferências."""
        code = self._authorize(user, branch=branch)
        wanted = _text(product_code)
        if not wanted:
            raise ValueError("Informe o código do produto.")
        cutoff = self._parse_cutoff(cutoff_date, cutoff_time)
        computed = self._load_requirements(branch=code, cutoff=cutoff, refresh=False)
        matched = [item for item in computed.items if item.product_code == wanted]
        if not matched:
            raise LookupError(
                setting_message(
                    "productNotInCutoff",
                    "Este produto não faz parte do corte atual.",
                )
            )

        names = {
            _text(center.get("work_center")): _text(center.get("work_center_name"))
            or _text(center.get("work_center"))
            for center in computed.work_centers
        }
        work_centers = [
            {
                "work_center": item.work_center,
                "work_center_name": names.get(item.work_center, item.work_center),
                "required_qty": item.required_qty,
                "to_deliver_qty": item.to_deliver_qty,
                "status": item.status,
            }
            for item in sorted(matched, key=lambda row: row.work_center)
        ]
        first = matched[0]
        warehouse = setting_str("sourceWarehouse", "01")
        return {
            "branch": code,
            "cutoff": self._cutoff_payload(cutoff),
            "product": {
                "code": first.product_code,
                "description": first.description,
                "unit": first.unit,
                "pickup_location": computed.pickup_locations.get(first.product_code, ""),
            },
            "work_centers": work_centers,
            "stock": self._product_stock(branch=code, product_code=wanted, warehouse=warehouse),
            "transfers": self._product_transfers(
                branch=code, product_code=wanted, cutoff=cutoff
            ),
        }

    def _product_stock(
        self,
        *,
        branch: str,
        product_code: str,
        warehouse: str,
    ) -> dict[str, Any]:
        """Saldo real do armazém 01 — não a fatia FIFO da grade."""
        try:
            payload = self._gateway.fetch_stock_balances_items(
                branch=branch,
                warehouse=warehouse,
                only_positive=False,
                page=1,
                page_size=max(setting_int("balancesPageSize", 500), 1),
                product_codes=[product_code],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("line_feeder_product_stock_unavailable: %s", exc)
            return {
                "available": False,
                "warehouse": warehouse,
                "quantity": None,
                "message": setting_message(
                    "productDetailStockUnavailable",
                    "Não foi possível ler o saldo do almoxarifado agora.",
                ),
            }
        quantity = 0.0
        for row in _items(payload):
            if _text(row.get("product_code")) != product_code:
                continue
            quantity += _number(row.get("quantity"))
        return {
            "available": True,
            "warehouse": warehouse,
            "quantity": round(quantity, 6),
        }

    def _product_transfers(
        self,
        *,
        branch: str,
        product_code: str,
        cutoff: datetime,
    ) -> dict[str, Any]:
        lookback = max(setting_int("productDetailLookbackDays", 30), 1)
        page_size = max(setting_int("productDetailTransferPageSize", 20), 1)
        end_date = cutoff.date().isoformat()
        start_date = (cutoff.date() - timedelta(days=lookback)).isoformat()
        try:
            payload = self._gateway.fetch_product_internal_movements(
                product_code=product_code,
                branch=branch,
                kind=MOVEMENT_KIND_WAREHOUSE_TRANSFER,
                start_date=start_date,
                end_date=end_date,
                page=1,
                page_size=page_size,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("line_feeder_product_transfers_unavailable: %s", exc)
            return {
                "available": False,
                "items": [],
                "message": setting_message(
                    "productDetailTransfersUnavailable",
                    "Não foi possível ler as transferências recentes.",
                ),
            }
        return {
            "available": True,
            "items": pair_warehouse_transfers(_items(payload), limit=page_size),
        }

    def _load_requirements(
        self,
        *,
        branch: str,
        cutoff: datetime,
        refresh: bool,
    ) -> _Requirements:
        """O cálculo é global no corte; o recorte da tela vem depois do rateio."""
        cache_key = f"{branch}|{cutoff.isoformat()}"
        if not refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        operations, work_centers = self._eligible_operations(branch=branch, cutoff=cutoff)
        if not operations:
            computed = _Requirements(
                items=(),
                work_centers=work_centers,
                operation_count=0,
                order_count=0,
                balances_available=True,
                truncated_orders=False,
                pickup_locations={},
            )
            self._cache.set(cache_key, computed)
            return computed

        orders, truncated = self._orders_for_batch(operations)
        commitments = self._fetch_commitments(branch=branch, production_orders=orders)
        product_codes = sorted(
            {
                _text(item.get("product_code"))
                for rows in commitments.values()
                for item in rows
                if _text(item.get("product_code"))
            }
        )

        point_of_use, source, balances_available = self._fetch_balances(
            branch=branch, product_codes=product_codes
        )
        pickup_locations = self._fetch_pickup_locations(
            branch=branch, product_codes=product_codes
        )

        items = build_requirements(
            operations,
            commitments_by_operation=commitments,
            point_of_use_balances=point_of_use,
            source_balances=source,
            balances_available=balances_available,
        )
        computed = _Requirements(
            items=tuple(items),
            work_centers=work_centers,
            operation_count=len(operations),
            order_count=len(orders),
            balances_available=balances_available,
            truncated_orders=truncated,
            pickup_locations=pickup_locations,
        )
        self._cache.set(cache_key, computed)
        return computed

    def _eligible_operations(
        self,
        *,
        branch: str,
        cutoff: datetime,
    ) -> tuple[list[dict[str, Any]], tuple[dict[str, str], ...]]:
        row = self._snapshots.get(branch=branch)
        if row is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi publicada pelo PCP."
            )
        payload = decode_snapshot_payload(row)
        # Conjunto retirado da programação não gera necessidade de material.
        operations = visible_operations(
            payload_operations(payload), withdrawn_order_numbers(payload)
        )
        eligible = filter_by_cutoff(operations, cutoff=cutoff)
        centers = self._work_center_catalog(payload, eligible)
        return eligible, centers

    @staticmethod
    def _work_center_catalog(
        payload: dict[str, Any],
        operations: list[dict[str, Any]],
    ) -> tuple[dict[str, str], ...]:
        """Só as bancadas com operação no corte — filtro que não leva a lugar nenhum confunde."""
        names = {
            _text(item.get("work_center")): _text(item.get("work_center_name"))
            for item in payload_work_centers(payload)
            if _text(item.get("work_center"))
        }
        present: list[str] = []
        for item in operations:
            center = _text(item.get("work_center"))
            if center and center not in present:
                present.append(center)
        present.sort()
        return tuple(
            {"work_center": center, "work_center_name": names.get(center, "")}
            for center in present
        )

    @staticmethod
    def _orders_for_batch(operations: list[dict[str, Any]]) -> tuple[list[str], bool]:
        """Lista única de OPs do corte, respeitando o teto de lotes por leitura.

        Um corte normal da filial passa de 500 OPs, acima do teto por requisição
        da api-delpi: quem fatia é o BFF (ver ``_fetch_commitments``). O teto aqui
        é só o limite de quantos lotes uma leitura pode custar.
        """
        ceiling = _commitment_batch_size() * max(setting_int("maxCommitmentBatches", 30), 1)
        orders: list[str] = []
        seen: set[str] = set()
        for item in operations:
            order = _text(item.get("production_order"))
            if order and order not in seen:
                seen.add(order)
                orders.append(order)
        if len(orders) <= ceiling:
            return orders, False
        return orders[:ceiling], True

    def _fetch_commitments(
        self,
        *,
        branch: str,
        production_orders: Sequence[str],
    ) -> dict[tuple[str, str], list[dict[str, Any]]]:
        """Sem empenho não há cockpit: esta falha não degrada, propaga.

        O teto de OPs por requisição é contrato da api-delpi, não limite do corte:
        a lista é fatiada aqui e os lotes são disjuntos por OP, então o índice de
        (OP, operação) só recebe chaves novas a cada fatia.

        O custo do empenho é ~45 ms por OP, linear: um corte de 550 OPs em série
        passava de 20 s. Os lotes vão em paralelo com pool limitado, como o
        progresso do mapa de entrega.
        """
        size = _commitment_batch_size()
        orders = list(production_orders)
        chunks = [orders[start : start + size] for start in range(0, len(orders), size)]
        commitments: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for payload in self._fan_out(
            lambda chunk: self._gateway.fetch_operation_materials_batch(
                branch=branch,
                production_orders=chunk,
            ),
            chunks,
            failure="Não foi possível carregar os empenhos das ordens de produção.",
        ):
            commitments.update(normalize_commitments(_items(payload)))
        return commitments

    @staticmethod
    def _fan_out(
        call: Callable[[Any], Any],
        arguments: Sequence[Any],
        *,
        failure: str,
        max_workers: int | None = None,
    ) -> list[Any]:
        """Leituras independentes em paralelo, com teto de workers.

        A primeira falha vira ``DelpiGatewayError``: bloco incompleto não é bloco
        degradado, e quem decide degradar é o chamador.
        """
        if not arguments:
            return []
        try:
            if len(arguments) == 1:
                return [call(arguments[0])]
            limit = max_workers or setting_int("fetchMaxWorkers", 6)
            workers = max(1, min(limit, len(arguments)))
            with ThreadPoolExecutor(
                max_workers=workers,
                initializer=_caller_context_initializer(),
            ) as pool:
                return list(pool.map(call, arguments))
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(failure) from exc

    def _fetch_balances(
        self,
        *,
        branch: str,
        product_codes: list[str],
    ) -> tuple[dict[str, float], dict[str, float], bool]:
        """Saldo é bloco degradável: sem ele a necessidade ainda responde.

        Os dois armazéns são leituras independentes: vão em paralelo.
        """
        if not product_codes:
            return {}, {}, True
        warehouses = (
            setting_str("pointOfUseWarehouse", "99"),
            setting_str("sourceWarehouse", "01"),
        )
        try:
            point_of_use, source = self._fan_out(
                lambda warehouse: self._fetch_warehouse_balances(
                    branch=branch,
                    warehouse=warehouse,
                    product_codes=product_codes,
                ),
                warehouses,
                failure="Não foi possível carregar os saldos por armazém.",
                max_workers=len(warehouses),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("line_feeder_balances_unavailable: %s", exc)
            return {}, {}, False
        return point_of_use, source, True

    def _fetch_warehouse_balances(
        self,
        *,
        branch: str,
        warehouse: str,
        product_codes: list[str],
    ) -> dict[str, float]:
        """Saldo por produto no armazém. ``only_positive=False`` para distinguir
        zero de negativo — negativo no armazém não é material disponível."""
        page_size = max(setting_int("balancesPageSize", 500), 1)
        max_pages = max(setting_int("maxBalancePages", 20), 1)
        balances: dict[str, float] = {}
        page = 1
        while page <= max_pages:
            payload = self._gateway.fetch_stock_balances_items(
                branch=branch,
                warehouse=warehouse,
                only_positive=False,
                page=page,
                page_size=page_size,
                product_codes=product_codes,
            )
            rows = _items(payload)
            for row in rows:
                code = _text(row.get("product_code"))
                if not code:
                    continue
                balances[code] = balances.get(code, 0.0) + _number(row.get("quantity"))
            if len(rows) < page_size:
                break
            page += 1
        return balances

    def _fetch_pickup_locations(
        self,
        *,
        branch: str,
        product_codes: list[str],
    ) -> dict[str, str]:
        """Local de retirada (BZ_MPLOCAL). Bloco degradável: lista nasce sem local."""
        if not product_codes:
            return {}
        try:
            payload = self._gateway.fetch_product_physical_locations(
                branch=branch,
                product_codes=product_codes,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("line_feeder_pickup_locations_unavailable: %s", exc)
            return {}
        locations: dict[str, str] = {}
        for row in _items(payload):
            code = _text(row.get("product_code"))
            if not code:
                continue
            locations[code] = _text(row.get("physical_location"))
        return locations

    # ------------------------------------------------------------------ #
    # Lista de coleta
    # ------------------------------------------------------------------ #

    def create_pick_plan(
        self,
        user: object | None,
        *,
        branch: str,
        cutoff_date: str | None,
        cutoff_time: str | None,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        cutoff = self._parse_cutoff(cutoff_date, cutoff_time)
        computed = self._load_requirements(branch=code, cutoff=cutoff, refresh=True)
        if not computed.balances_available:
            # Lista de coleta sem saldo medido mandaria buscar o que já está na bancada.
            raise DelpiGatewayError(
                setting_message(
                    "balancesUnavailable",
                    "Não foi possível ler o estoque agora.",
                )
            )

        center = _text(work_center)
        candidates = pick_list_candidates(
            filter_requirements(list(computed.items), work_center=center or None)
        )
        lines = pick_list_by_product(candidates)
        if not lines:
            raise ValueError(
                setting_message("planEmpty", "Não há material a entregar neste horário.")
            )

        max_items = max(setting_int("maxPickItems", 500), 1)
        located = [
            line.with_pickup_location(
                computed.pickup_locations.get(line.product_code, "")
            )
            for line in lines[:max_items]
        ]
        plan = self._pick_plans.create_plan(
            branch=code,
            cutoff_at=cutoff,
            work_center=center or None,
            created_by=_actor(user),
            items=[_pick_item_row(line) for line in located],
        )
        return self._plan_payload(plan)

    def list_pick_plans(
        self,
        user: object | None,
        *,
        branch: str,
        status: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        wanted = _text(status).lower()
        if wanted and wanted not in PLAN_STATUSES:
            raise ValueError("Situação inválida para a lista de coleta.")
        plans = self._pick_plans.list_plans(
            branch=code, status=wanted or None, limit=limit
        )
        return {
            "branch": code,
            "filters": {"status": wanted},
            "items": [_plan_summary(plan) for plan in plans],
            "item_statuses": setting_map("itemStatuses"),
        }

    def get_pick_plan(
        self,
        user: object | None,
        *,
        branch: str,
        plan_id: str,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        plan = self._pick_plans.get_plan(plan_id=_require_id(plan_id), branch=code)
        if plan is None:
            raise LookupError(
                setting_message("planNotFound", "Lista de coleta não encontrada.")
            )
        return self._plan_payload(plan)

    def update_pick_item_status(
        self,
        user: object | None,
        *,
        branch: str,
        plan_id: str,
        item_id: str,
        status: str,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        wanted = _text(status).lower()
        if wanted not in ITEM_STATUSES:
            raise ValueError(
                setting_message("invalidItemStatus", "Situação inválida para o item.")
            )
        identifier = _require_id(plan_id)
        plan = self._pick_plans.get_plan(plan_id=identifier, branch=code)
        if plan is None:
            raise LookupError(
                setting_message("planNotFound", "Lista de coleta não encontrada.")
            )
        if _text(plan.get("status")) == "closed":
            raise ValueError(
                setting_message("planClosed", "Esta lista de coleta já foi fechada.")
            )

        item = self._pick_plans.update_item_status(
            plan_id=identifier,
            item_id=_require_id(item_id),
            branch=code,
            status=wanted,
            updated_by=_actor(user),
        )
        if item is None:
            raise LookupError(
                setting_message("itemNotFound", "Item não encontrado nesta lista.")
            )
        return {
            "branch": code,
            "plan_id": identifier,
            "item": _pick_item_payload(item),
        }

    def close_pick_plan(
        self,
        user: object | None,
        *,
        branch: str,
        plan_id: str,
    ) -> dict[str, Any]:
        code = self._authorize(user, branch=branch)
        plan = self._pick_plans.close_plan(
            plan_id=_require_id(plan_id),
            branch=code,
            updated_by=_actor(user),
        )
        if plan is None:
            raise LookupError(
                setting_message("planNotFound", "Lista de coleta não encontrada.")
            )
        return {"branch": code, "plan": _plan_summary(plan)}

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _plan_payload(self, plan: dict[str, Any]) -> dict[str, Any]:
        items = [_pick_item_payload(item) for item in plan.get("items") or []]
        return {
            "plan": _plan_summary(plan, items=items),
            "items": items,
            "item_statuses": setting_map("itemStatuses"),
        }

    @staticmethod
    def _parse_cutoff(cutoff_date: str | None, cutoff_time: str | None) -> datetime:
        try:
            return parse_cutoff(cutoff_date, cutoff_time)
        except ValueError as exc:
            raise ValueError(
                str(exc)
                or setting_message("cutoffRequired", "Escolha a data e a hora do corte.")
            ) from exc

    @staticmethod
    def _cutoff_payload(cutoff: datetime) -> dict[str, str]:
        return {
            "at": cutoff.isoformat(),
            "date": cutoff.date().isoformat(),
            "time": cutoff.strftime("%H:%M"),
        }

    @staticmethod
    def _normalize_requirement_status(status: str | None) -> str | None:
        wanted = _text(status).lower()
        if not wanted or wanted == "all":
            return None
        if wanted not in setting_map("statuses"):
            raise ValueError("Situação inválida para o material.")
        return wanted


def _caller_context_initializer() -> Callable[[], None]:
    """Replica o contexto de quem pediu em cada worker do pool.

    ``contextvars`` não são herdadas por thread: sem isto o gateway perderia o
    JWT do usuário justamente nas fatias paralelas, e a mesma rota trocaria a
    identidade do usuário pelo token de serviço só porque o corte ficou grande.
    A captura tem de acontecer aqui, na thread chamadora — dentro do worker ela
    copiaria o contexto vazio dele. Cada worker escreve no próprio contexto, em
    vez de compartilhar um ``Context``, que não pode ser entrado por duas
    threads ao mesmo tempo.
    """
    snapshot = list(copy_context().items())

    def initialize() -> None:
        for variable, value in snapshot:
            variable.set(value)

    return initialize


def _commitment_batch_size() -> int:
    """Lote menor que o teto da api-delpi: são vários em paralelo, não um só."""
    cap = max(setting_int("maxProductionOrdersPerBatch", 300), 1)
    return max(1, min(setting_int("commitmentBatchSize", 100), cap))


def _requirement_payload(
    item: MaterialRequirement,
    locations: dict[str, str],
) -> dict[str, Any]:
    payload = item.as_dict()
    payload["pickup_location"] = locations.get(item.product_code, "")
    return payload


def _pick_item_row(item: ProductPickLine) -> dict[str, Any]:
    return {
        "product_code": item.product_code,
        "description": item.description,
        "unit": item.unit,
        "pickup_location": item.pickup_location,
        "required_qty": item.required_qty,
        "point_of_use_qty": item.point_of_use_qty,
        "to_deliver_qty": item.to_deliver_qty,
    }


def _pick_item_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _text(row.get("id")),
        "product_code": _text(row.get("product_code")),
        "description": _text(row.get("description")),
        "unit": _text(row.get("unit")),
        "pickup_location": _text(row.get("pickup_location")),
        "required_qty": _number(row.get("required_qty")),
        "point_of_use_qty": _number(row.get("point_of_use_qty")),
        "to_deliver_qty": _number(row.get("to_deliver_qty")),
        "status": _text(row.get("status")) or "pending",
        "updated_at": _iso(row.get("updated_at")),
        "updated_by": _text(row.get("updated_by")) or None,
    }


def _plan_summary(
    plan: dict[str, Any],
    *,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    counts = _status_counts(plan, items)
    return {
        "id": _text(plan.get("id")),
        "branch": _text(plan.get("branch")),
        "cutoff_at": _iso(plan.get("cutoff_at")),
        "work_center": _text(plan.get("work_center")) or None,
        "status": _text(plan.get("status")) or "open",
        "created_at": _iso(plan.get("created_at")),
        "created_by": _text(plan.get("created_by")) or None,
        "updated_at": _iso(plan.get("updated_at")),
        "updated_by": _text(plan.get("updated_by")) or None,
        **counts,
    }


def _status_counts(
    plan: dict[str, Any],
    items: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Contadores vêm do banco na listagem e dos itens quando o plano vem completo."""
    if items is None:
        return {
            "item_count": int(plan.get("item_count") or 0),
            "pending_count": int(plan.get("pending_count") or 0),
            "picked_count": int(plan.get("picked_count") or 0),
            "delivered_count": int(plan.get("delivered_count") or 0),
            "to_deliver_qty": _number(plan.get("to_deliver_qty")),
        }
    return {
        "item_count": len(items),
        "pending_count": sum(1 for item in items if item["status"] == "pending"),
        "picked_count": sum(1 for item in items if item["status"] == "picked"),
        "delivered_count": sum(1 for item in items if item["status"] == "delivered"),
        "to_deliver_qty": round(sum(item["to_deliver_qty"] for item in items), 6),
    }


def _items(payload: Any) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, dict) else None
    source = data if isinstance(data, dict) else payload
    rows = source.get("items") if isinstance(source, dict) else None
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _actor(user: object | None) -> str | None:
    for attribute in ("email", "username", "preferred_username", "sub"):
        value = _text(getattr(user, attribute, None))
        if value:
            return value[:120]
    return None


def _require_id(value: str | None) -> str:
    """Id malformado é pedido inválido, não erro de banco ao castar UUID."""
    identifier = _text(value)
    if not identifier:
        raise ValueError("Informe o identificador da lista de coleta.")
    try:
        return str(UUID(identifier))
    except ValueError as exc:
        raise ValueError("Identificador inválido para a lista de coleta.") from exc


def _iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float:
    try:
        return round(float(value or 0), 6)
    except (TypeError, ValueError):
        return 0.0
