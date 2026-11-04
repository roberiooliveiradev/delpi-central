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
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence
from uuid import UUID

from production_control_app.application.services.integration_batches import (
    commitment_batch_size,
    fan_out,
    max_commitment_batches,
)
from production_control_app.application.services.line_feeder_settings import (
    message as setting_message,
    setting_int,
    setting_map,
    setting_str,
)
from production_control_app.core.security import PC_LINE_FEEDER_VIEW, can
from production_control_app.domain.errors import (
    DelpiGatewayError,
    HorizonPreviewStale,
    SnapshotNotFound,
)
from production_control_app.domain.ports.line_feeder_pick_plan_repository import (
    LineFeederPickPlanRepositoryPort,
)
from production_control_app.domain.ports.machine_load_publication_repository import (
    MachineLoadPublicationRepositoryPort,
)
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.line_feeder_horizon import (
    HorizonOperationInput,
    allocate_work_center_horizon,
    work_center_result_payload,
)
from production_control_app.domain.services.line_feeder_materials import (
    CoveredOperationDemand,
    apply_factory_stock,
    build_material_demands,
    summarize_materials,
)
from production_control_app.domain.services.line_feeder_published_queue import (
    list_visible_published_queues,
    project_published_queue,
)
from production_control_app.domain.services.machine_load_transfer import (
    normalize_work_center,
)
from production_control_app.domain.services.production_run_standard_time import (
    normalize_standard_time_snapshot,
)
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
    withdrawn_marks,
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
    # product_code -> bloqueado para inventário no armazém 01; ausência = livre.
    inventory_blocks: dict[str, bool]


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
        publications: MachineLoadPublicationRepositoryPort | None = None,
        branch_access: BranchAccessService | None = None,
        cache: _RequirementsCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._snapshots = snapshots
        self._pick_plans = pick_plans
        self._publications = publications
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
    # Fila PUBLISHED (fundação para horizonte/materiais — Etapa 1)
    # ------------------------------------------------------------------ #

    def get_published_queue(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Leitura autenticada da fila PUBLISHED na ordem do operador.

        Nunca faz fallback para WORKING, nunca dispara refresh/publish e não
        reordena por ``scheduled_*`` do TOTVS. A revisão efetiva vem de
        ``row_version`` (xmin) — mutações LIVE mudam a revisão sem trocar
        ``generation_id``.
        """
        code = self._authorize(user, branch=branch)
        if self._publications is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        row = self._publications.get(branch=code)
        if row is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        return project_published_queue(
            row, branch=code, work_center=_text(work_center) or None
        )

    def preview_horizon(
        self,
        user: object | None,
        *,
        branch: str,
        work_centers: Sequence[str],
        hours_per_work_center: float,
    ) -> dict[str, Any]:
        """Prévia somente leitura: produção contemplada por CT no horizonte.

        Orçamento de horas é **por CT** (paralelo entre postos). Fonte da
        sequência: PUBLISHED. Saldos vivos: lote SH6/SC2. Tempo: standard-time
        S2S da api-delpi. Sem persistência e sem fallback WORKING.
        """
        code = self._authorize(user, branch=branch)
        centers = self._normalize_horizon_work_centers(work_centers)
        hours = self._normalize_horizon_hours(hours_per_work_center)
        if self._publications is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )

        row = self._publications.get(branch=code)
        if row is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        revision_start = _text(row.get("row_version"))
        queues = list_visible_published_queues(
            row, branch=code, work_centers=centers
        )
        self._assert_work_centers_in_publication(queues, centers)

        selected_queues = [
            group
            for group in queues["work_center_queues"]
            if group["work_center"] in set(centers)
        ]
        # Preserva a ordem pedida pelo cliente entre CTs; dentro do CT, a
        # ordem publicada.
        by_center = {group["work_center"]: group for group in selected_queues}
        ordered_queues = [
            by_center[center] for center in centers if center in by_center
        ]
        for center in centers:
            if center not in by_center:
                ordered_queues.append(
                    {
                        "work_center": center,
                        "work_center_name": "",
                        "operations": [],
                    }
                )

        total_ops = sum(len(group["operations"]) for group in ordered_queues)
        max_ops = setting_int("horizonMaxOperationsPerRequest", 500)
        if total_ops > max_ops:
            raise ValueError(
                f"A seleção excede o limite de {max_ops} operações por prévia."
            )

        flat_ops = [
            op for group in ordered_queues for op in group["operations"]
        ]
        balances_as_of = datetime.now(timezone.utc).isoformat()
        balance_map = self._fetch_live_operation_balances(
            branch=code, operations=flat_ops
        )

        st_cache: dict[tuple[str, str], dict[str, Any]] = {}
        st_calls = 0
        st_limit = setting_int("horizonMaxStandardTimeCalls", 200)
        ct_results: list[dict[str, Any]] = []
        preview_complete = True

        for group in ordered_queues:
            inputs: list[HorizonOperationInput] = []
            incomplete_reason: str | None = None
            for op in group["operations"]:
                key = (
                    _text(op.get("production_order")),
                    _text(op.get("operation_code")),
                )
                live = balance_map.get(key)
                if live is None:
                    pending = None
                    produced = None
                    balance_state = "unknown"
                else:
                    pending = _optional_decimal(live.get("operation_pending_qty"))
                    produced = _optional_decimal(live.get("operation_produced_qty"))
                    if pending is None:
                        balance_state = "unknown"
                    elif pending <= 0:
                        balance_state = "closed"
                    else:
                        balance_state = "open"

                if balance_state == "closed":
                    inputs.append(
                        self._horizon_input(
                            op,
                            pending_qty=Decimal("0"),
                            produced_qty=produced,
                            balance_state="closed",
                            ideal_cycle_seconds=None,
                            setup_seconds=None,
                            pieces_conversion_factor=_optional_decimal(
                                op.get("pieces_conversion_factor")
                            ),
                            standard_time_quality="n/a",
                            standard_time_source="n/a",
                        )
                    )
                    continue

                if balance_state == "unknown":
                    incomplete_reason = "balance_unknown"
                    preview_complete = False
                    break

                if key not in st_cache:
                    if st_calls >= st_limit:
                        incomplete_reason = "standard_time_call_limit"
                        preview_complete = False
                        break
                    st_cache[key] = self._lookup_standard_time(
                        branch=code,
                        production_order=key[0],
                        operation_code=key[1],
                    )
                    st_calls += 1
                snap = st_cache[key]
                quality = str(
                    snap.get("standard_time_data_quality_snapshot") or "upstream_unavailable"
                )
                factor = _optional_decimal(op.get("pieces_conversion_factor"))
                # Preferir fator do standard-time quando o snapshot não trouxe.
                if factor is None:
                    raw_st = snap.get("_raw") if isinstance(snap.get("_raw"), dict) else {}
                    factor = _optional_decimal(
                        (raw_st or {}).get("pieces_conversion_factor")
                    )
                inputs.append(
                    self._horizon_input(
                        op,
                        pending_qty=pending,
                        produced_qty=produced,
                        balance_state=balance_state,
                        ideal_cycle_seconds=_optional_decimal(
                            snap.get("ideal_cycle_seconds_snapshot")
                        ),
                        setup_seconds=_optional_decimal(
                            snap.get("setup_seconds_snapshot")
                        ),
                        pieces_conversion_factor=factor,
                        standard_time_quality=quality,
                        standard_time_source=str(
                            snap.get("standard_time_source") or "unavailable"
                        ),
                    )
                )

            result = allocate_work_center_horizon(
                inputs,
                hours=hours,
                work_center=group["work_center"],
                work_center_name=_text(group.get("work_center_name")),
            )
            payload = work_center_result_payload(result)
            if incomplete_reason and result.completeness == "complete":
                payload["completeness"] = "incomplete"
                payload["stop_reason"] = incomplete_reason
                preview_complete = False
            elif result.completeness != "complete":
                preview_complete = False
            ct_results.append(payload)

        row_end = self._publications.get(branch=code)
        if row_end is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        revision_end = _text(row_end.get("row_version"))
        if revision_start != revision_end:
            raise HorizonPreviewStale(
                "A programação publicada mudou durante a prévia. Consulte novamente."
            )

        return {
            "branch": code,
            "hours_per_work_center": hours,
            "publication": {
                "generation_id": _text(row.get("generation_id")) or None,
                "publication_revision": revision_end or None,
                "published_at": _iso(row.get("published_at")),
            },
            "balances_as_of": balances_as_of,
            "sources": {
                "queue": "published",
                "balances": "api-delpi:machine-load/operation-balances",
                "standard_time": "api-delpi:get_production_operation_standard_time",
            },
            "temporal_projection": {
                "mode": "relative_offsets",
                "note": (
                    "Offsets em segundos a partir do início do horizonte por CT. "
                    "Não são horários absolutos de fábrica (sem turno/calendário/paradas)."
                ),
            },
            "setup_policy": {
                "waived_when": "operation_produced_qty > 0",
                "applicable_when": "operation_produced_qty == 0",
                "uncertain_when": "operation_produced_qty ausente na consulta de saldos",
            },
            "preview_completeness": (
                "complete" if preview_complete else "incomplete"
            ),
            "standard_time_calls": st_calls,
            "work_centers": ct_results,
        }

    def preview_materials(
        self,
        user: object | None,
        *,
        branch: str,
        work_centers: Sequence[str],
        hours_per_work_center: float,
    ) -> dict[str, Any]:
        """Prévia dinâmica de materiais — saldo real do ponto de uso (99).

        Reutiliza o horizonte (E2). Empenhos SD4 vigentes. Não persiste lista,
        não usa status de coleta e não desconta o almoxarifado (01) da falta.
        """
        horizon = self.preview_horizon(
            user,
            branch=branch,
            work_centers=work_centers,
            hours_per_work_center=hours_per_work_center,
        )
        code = _text(horizon.get("branch"))
        expected_revision = _text(
            (horizon.get("publication") or {}).get("publication_revision")
        )
        # shortfall (fila menor que as horas) é válido para materiais: toda a
        # produção disponível já entrou. incomplete (saldo/ST) bloqueia a lista.
        horizon_safe = all(
            group.get("completeness") != "incomplete"
            for group in (horizon.get("work_centers") or [])
        )

        covered_ops: list[CoveredOperationDemand] = []
        for group in horizon.get("work_centers") or []:
            for op in group.get("operations") or []:
                covered = _optional_decimal(op.get("covered_qty"))
                pending = _optional_decimal(op.get("pending_qty"))
                if covered is None or pending is None:
                    continue
                if covered <= 0:
                    continue
                covered_ops.append(
                    CoveredOperationDemand(
                        work_center=_text(op.get("work_center")),
                        work_center_name=_text(op.get("work_center_name")),
                        production_order=_text(op.get("production_order")),
                        operation_code=_text(op.get("operation_code")),
                        operation_id=_text(op.get("operation_id")),
                        sequence_position=int(op.get("sequence_position") or 0),
                        covered_qty=covered,
                        pending_qty=pending,
                    )
                )

        orders: list[str] = []
        seen_orders: set[str] = set()
        for op in covered_ops:
            if op.production_order and op.production_order not in seen_orders:
                seen_orders.add(op.production_order)
                orders.append(op.production_order)
        ceiling = commitment_batch_size() * max_commitment_batches()
        if len(orders) > ceiling:
            raise ValueError(
                "A prévia de materiais excede o limite de ordens consultáveis "
                f"({ceiling}). Reduza o horizonte ou a seleção de postos."
            )

        commitments = (
            self._fetch_commitments(branch=code, production_orders=orders)
            if orders
            else {}
        )
        buckets, demand_warnings, proportional_ok = build_material_demands(
            covered_ops, commitments
        )
        product_codes = sorted({bucket.product_code for bucket in buckets})
        stock_as_of = datetime.now(timezone.utc).isoformat()
        factory, source, balances_available, stock_complete = (
            self._fetch_balances_for_materials(
                branch=code, product_codes=product_codes
            )
        )
        locations = self._fetch_pickup_locations(
            branch=code, product_codes=product_codes
        )
        inventory_blocks = self._fetch_inventory_blocks(
            branch=code, product_codes=product_codes
        )

        items = apply_factory_stock(
            buckets,
            factory_balances=factory if balances_available else None,
            source_balances=source if balances_available else None,
            balances_available=balances_available and stock_complete,
        )
        for item in items:
            code_prod = item["product_code"]
            item["pickup_location"] = locations.get(code_prod, "")
            item["inventory_blocked"] = bool(
                inventory_blocks.get(code_prod, False)
            )

        if self._publications is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        row_end = self._publications.get(branch=code)
        if row_end is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        revision_end = _text(row_end.get("row_version"))
        if expected_revision and revision_end != expected_revision:
            raise HorizonPreviewStale(
                "A programação publicada mudou durante a prévia de materiais. "
                "Consulte novamente."
            )

        complete = (
            horizon_safe
            and proportional_ok
            and balances_available
            and stock_complete
        )
        stop_reasons: list[str] = []
        if not horizon_safe:
            stop_reasons.append("horizon_incomplete")
        if not proportional_ok:
            stop_reasons.append("proportional_demand_incomplete")
        if not balances_available:
            stop_reasons.append("stock_unavailable")
        elif not stock_complete:
            stop_reasons.append("stock_pagination_incomplete")

        return {
            "branch": code,
            "hours_per_work_center": horizon.get("hours_per_work_center"),
            "publication": horizon.get("publication"),
            "horizon_balances_as_of": horizon.get("balances_as_of"),
            "stock_as_of": stock_as_of,
            "sources": {
                "queue": "published",
                "horizon": "line_feeder_horizon",
                "commitments": "api-delpi:operation-materials/batch",
                "factory_stock": "api-delpi:stock-balances/items",
                "point_of_use_warehouse": setting_str("pointOfUseWarehouse", "99"),
                "source_warehouse": setting_str("sourceWarehouse", "01"),
            },
            "business_rule": {
                "to_collect": "max(0, required_from_horizon - factory_available)",
                "factory_stock_authority": True,
                "prior_pick_lists_do_not_reduce_demand": True,
                "source_warehouse_informational_only": True,
            },
            "preview_completeness": "complete" if complete else "incomplete",
            "operational_list_safe": complete,
            "stop_reasons": stop_reasons,
            "demand_warnings": demand_warnings,
            "horizon": {
                "preview_completeness": horizon.get("preview_completeness"),
                "work_centers": [
                    {
                        "work_center": group.get("work_center"),
                        "completeness": group.get("completeness"),
                        "hours_covered": group.get("hours_covered"),
                        "operation_count": len(group.get("operations") or []),
                        "stop_reason": group.get("stop_reason"),
                    }
                    for group in horizon.get("work_centers") or []
                ],
                "covered_operation_count": len(covered_ops),
            },
            "summary": summarize_materials(items),
            "materials": items,
        }

    # ------------------------------------------------------------------ #
    # Horizonte — helpers
    # ------------------------------------------------------------------ #

    def _normalize_horizon_work_centers(self, work_centers: Sequence[str]) -> list[str]:
        if not work_centers:
            raise ValueError("Informe ao menos um centro de trabalho.")
        max_centers = setting_int("horizonMaxWorkCenters", 40)
        if len(work_centers) > max_centers:
            raise ValueError(
                f"Selecione no máximo {max_centers} centros de trabalho por prévia."
            )
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in work_centers:
            center = normalize_work_center(raw)
            if not center:
                raise ValueError("Centro de trabalho inválido na seleção.")
            if center in seen:
                raise ValueError(
                    f"Centro de trabalho duplicado na seleção: {center}."
                )
            seen.add(center)
            normalized.append(center)
        return normalized

    def _normalize_horizon_hours(self, hours: float) -> float:
        try:
            value = float(hours)
        except (TypeError, ValueError) as exc:
            raise ValueError("Informe um horizonte de horas numérico.") from exc
        if value != value or value <= 0:  # NaN or non-positive
            raise ValueError("O horizonte em horas deve ser finito e positivo.")
        ceiling = float(setting_int("horizonMaxHoursPerWorkCenter", 24))
        if value > ceiling:
            raise ValueError(
                f"O horizonte máximo por centro de trabalho é {ceiling:g} horas."
            )
        return value

    @staticmethod
    def _assert_work_centers_in_publication(
        queues: dict[str, Any],
        centers: Sequence[str],
    ) -> None:
        available = {
            normalize_work_center(item.get("work_center"))
            for item in queues.get("available_work_centers") or []
            if normalize_work_center(item.get("work_center"))
        }
        # Também aceita CT que só aparece nas operações (catálogo vazio).
        for group in queues.get("work_center_queues") or []:
            center = normalize_work_center(group.get("work_center"))
            if center:
                available.add(center)
        missing = [center for center in centers if center not in available]
        if missing:
            raise ValueError(
                "Centro(s) fora da programação publicada: "
                + ", ".join(missing)
                + "."
            )

    def _fetch_live_operation_balances(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        pairs: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for item in operations:
            key = (
                _text(item.get("production_order")),
                _text(item.get("operation_code")),
            )
            if not all(key) or key in seen:
                continue
            seen.add(key)
            pairs.append(
                {"production_order": key[0], "operation_code": key[1]}
            )
        if not pairs:
            return {}
        try:
            payload = self._gateway.fetch_machine_load_operation_balances(
                branch=branch, items=pairs
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível consultar os saldos das operações."
            ) from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        source = data if isinstance(data, dict) else payload
        rows = source.get("items") if isinstance(source, dict) else None
        result: dict[tuple[str, str], dict[str, Any]] = {}
        if not isinstance(rows, list):
            raise DelpiGatewayError(
                "Resposta inválida dos saldos de operação."
            )
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            key = (
                _text(raw.get("production_order")),
                _text(raw.get("operation_code")),
            )
            if all(key):
                result[key] = raw
        # Pares sem retorno = desconhecido (não inventar zero).
        return result

    def _lookup_standard_time(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        lookup = getattr(self._gateway, "fetch_operation_standard_time", None)
        if not callable(lookup):
            return normalize_standard_time_snapshot(None)
        try:
            raw = lookup(
                branch=branch,
                production_order=production_order,
                operation_code=operation_code,
            )
        except DelpiGatewayError as exc:
            snap = normalize_standard_time_snapshot(None)
            if exc.status_code == 404:
                snap["standard_time_data_quality_snapshot"] = (
                    "standard_time_unavailable"
                )
            return snap
        except Exception:  # noqa: BLE001
            return normalize_standard_time_snapshot(None)
        snap = normalize_standard_time_snapshot(raw if isinstance(raw, dict) else None)
        snap["_raw"] = raw if isinstance(raw, dict) else {}
        return snap

    @staticmethod
    def _horizon_input(
        op: dict[str, Any],
        *,
        pending_qty: Decimal | None,
        produced_qty: Decimal | None,
        balance_state: str,
        ideal_cycle_seconds: Decimal | None,
        setup_seconds: Decimal | None,
        pieces_conversion_factor: Decimal | None,
        standard_time_quality: str,
        standard_time_source: str,
    ) -> HorizonOperationInput:
        return HorizonOperationInput(
            operation_id=_text(op.get("operation_id")),
            sequence_position=int(op.get("sequence_position") or 0),
            work_center=_text(op.get("work_center")),
            work_center_name=_text(op.get("work_center_name")),
            production_order=_text(op.get("production_order")),
            operation_code=_text(op.get("operation_code")),
            product_code=_text(op.get("product_code")),
            unit=_text(op.get("unit")),
            pending_qty=pending_qty,
            produced_qty=produced_qty,
            balance_state=balance_state,
            ideal_cycle_seconds=ideal_cycle_seconds,
            setup_seconds=setup_seconds,
            pieces_conversion_factor=pieces_conversion_factor,
            standard_time_quality=standard_time_quality,
            standard_time_source=standard_time_source,
        )

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
        blocks = computed.inventory_blocks
        items_payload = [
            _requirement_payload(item, locations, blocks) for item in visible
        ]
        groups = group_by_work_center(visible)
        for group in groups:
            group["items"] = [
                {
                    **row,
                    "pickup_location": locations.get(row.get("product_code") or "", ""),
                    "inventory_blocked": bool(
                        blocks.get(row.get("product_code") or "", False)
                    ),
                }
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
                "inventory_blocked": bool(
                    computed.inventory_blocks.get(first.product_code, False)
                ),
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
                inventory_blocks={},
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
        inventory_blocks = self._fetch_inventory_blocks(
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
            inventory_blocks=inventory_blocks,
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
            payload_operations(payload), withdrawn_marks(payload)
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
        ceiling = commitment_batch_size() * max_commitment_batches()
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
        size = commitment_batch_size()
        orders = list(production_orders)
        chunks = [orders[start : start + size] for start in range(0, len(orders), size)]
        commitments: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for payload in fan_out(
            lambda chunk: self._gateway.fetch_operation_materials_batch(
                branch=branch,
                production_orders=chunk,
            ),
            chunks,
            failure="Não foi possível carregar os empenhos das ordens de produção.",
        ):
            commitments.update(normalize_commitments(_items(payload)))
        return commitments

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
            point_of_use, source = fan_out(
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

    def _fetch_balances_for_materials(
        self,
        *,
        branch: str,
        product_codes: list[str],
    ) -> tuple[dict[str, float], dict[str, float], bool, bool]:
        """Estoque para E3: (fábrica, almox, available, pagination_complete).

        Falha de integração → available=False (não inventar zero). Paginação
        estourada → complete=False (não omitir saldo silenciosamente).
        """
        if not product_codes:
            return {}, {}, True, True
        warehouses = (
            setting_str("pointOfUseWarehouse", "99"),
            setting_str("sourceWarehouse", "01"),
        )
        try:
            results = fan_out(
                lambda warehouse: self._fetch_warehouse_balances_complete(
                    branch=branch,
                    warehouse=warehouse,
                    product_codes=product_codes,
                ),
                warehouses,
                failure="Não foi possível carregar os saldos por armazém.",
                max_workers=len(warehouses),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("line_feeder_materials_balances_unavailable: %s", exc)
            return {}, {}, False, False
        point_of_use, pu_complete = results[0]
        source, source_complete = results[1]
        return point_of_use, source, True, bool(pu_complete and source_complete)

    def _fetch_warehouse_balances(
        self,
        *,
        branch: str,
        warehouse: str,
        product_codes: list[str],
    ) -> dict[str, float]:
        """Saldo por produto no armazém. ``only_positive=False`` para distinguir
        zero de negativo — negativo no armazém não é material disponível."""
        balances, _complete = self._fetch_warehouse_balances_complete(
            branch=branch, warehouse=warehouse, product_codes=product_codes
        )
        return balances

    def _fetch_warehouse_balances_complete(
        self,
        *,
        branch: str,
        warehouse: str,
        product_codes: list[str],
    ) -> tuple[dict[str, float], bool]:
        """Retorna saldos + se a paginação terminou sem truncar no teto local."""
        page_size = max(setting_int("balancesPageSize", 500), 1)
        max_pages = max(setting_int("maxBalancePages", 20), 1)
        balances: dict[str, float] = {}
        page = 1
        complete = True
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
            if page == max_pages:
                complete = False
                break
            page += 1
        return balances, complete

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

    def _fetch_inventory_blocks(
        self,
        *,
        branch: str,
        product_codes: list[str],
    ) -> dict[str, bool]:
        """Bloqueio de inventário no armazém fonte. Bloco degradável: ausência = livre."""
        if not product_codes:
            return {}
        warehouse = setting_str("sourceWarehouse", "01")
        try:
            payload = self._gateway.fetch_product_inventory_blocks(
                branch=branch,
                product_codes=product_codes,
                warehouse=warehouse,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("line_feeder_inventory_blocks_unavailable: %s", exc)
            return {}
        blocks: dict[str, bool] = {}
        for row in _items(payload):
            code = _text(row.get("product_code"))
            if not code:
                continue
            blocks[code] = bool(row.get("inventory_blocked"))
        return blocks

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


def _requirement_payload(
    item: MaterialRequirement,
    locations: dict[str, str],
    inventory_blocks: dict[str, bool] | None = None,
) -> dict[str, Any]:
    payload = item.as_dict()
    payload["pickup_location"] = locations.get(item.product_code, "")
    payload["inventory_blocked"] = bool(
        (inventory_blocks or {}).get(item.product_code, False)
    )
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


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return number


def _number(value: Any) -> float:
    try:
        return round(float(value or 0), 6)
    except (TypeError, ValueError):
        return 0.0
