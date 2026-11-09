"""Demanda — orquestração da carteira a entregar para o PCP.

A api-delpi entrega o dump TOTVS inteiro, sem filtro nem paginação. Todo o
recorte (filial, origem, busca, status, janela de entrega), a ordenação, a
página e os KPIs são resolvidos aqui, sobre um cache curto por processo.

Etapa 3: ``origin=protheus|myweg|both`` (default ``protheus`` = compatível).
MyWEG reusa source + adapter + ``DemandCoverageService`` (estoque; OP off).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterable

from production_control_app.application.services.demand_settings import (
    setting_int,
    setting_list,
    setting_str,
)
from production_control_app.core.security import (
    PC_DEMAND_VIEW,
    PC_MYWEG_NEEDS_VIEW,
    can,
)
from production_control_app.domain.errors import DelpiGatewayError, InvalidBranch
from production_control_app.domain.myweg_demand_source_contract import DEMAND_SOURCE_BRANCH
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.current_month_period import today_in_timezone
from production_control_app.domain.services.op_pendency_service import build_op_pendencies
from production_control_app.domain.services.stock_rupture_pendency_service import (
    build_stock_rupture_pendencies,
    merge_pendency_items,
)
from production_control_app.domain.services.demand_coverage_service import (
    STATUS_AT_RISK,
    STATUS_COVERED_BY_ORDER,
    STATUS_COVERED_BY_STOCK,
    STATUS_LATE,
    DemandCoverageService,
    DemandLine,
)

_FAR_FUTURE = date(9999, 12, 31)
ORIGIN_PROTHEUS = "protheus"
ORIGIN_MYWEG = "myweg"
ORIGIN_BOTH = "both"
ALLOWED_ORIGINS = frozenset({ORIGIN_PROTHEUS, ORIGIN_MYWEG, ORIGIN_BOTH})


def _unwrap(payload: Any, key: str) -> list[Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    source = data if isinstance(data, dict) else payload
    items = source.get(key) if isinstance(source, dict) else None
    return items if isinstance(items, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _iso_date(value: Any) -> date | None:
    text = _text(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class DemandQuery:
    branch: str
    search: str = ""
    status: str = ""
    due_from: date | None = None
    due_to: date | None = None
    sort: str = ""
    direction: str = "asc"
    page: int = 1
    page_size: int = 0
    origin: str = ORIGIN_PROTHEUS


class _DemandSnapshotCache:
    """Cache por chave (filial|origem) com TTL — evita repetir o dump a cada filtro/página."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        # (stored_at, lines, meta)
        self._entries: dict[str, tuple[float, list[DemandLine], dict[str, Any] | None]] = {}

    def get(self, key: str) -> list[DemandLine] | None:
        entry = self.get_entry(key)
        return None if entry is None else entry[0]

    def get_entry(
        self, key: str
    ) -> tuple[list[DemandLine], dict[str, Any] | None] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, lines, meta = entry
        if self._ttl and (time.monotonic() - stored_at) > self._ttl:
            self._entries.pop(key, None)
            return None
        return lines, meta

    def set(
        self,
        key: str,
        lines: list[DemandLine],
        meta: dict[str, Any] | None = None,
    ) -> None:
        self._entries[key] = (time.monotonic(), lines, meta)

    def clear(self) -> None:
        self._entries.clear()


_SNAPSHOT_CACHE = _DemandSnapshotCache(setting_int("cacheTtlSeconds", 120))


class _StockRuptureSnapshotCache:
    """TTL curto para evitar repetir a projeção de estoque em cada navegação."""

    def __init__(self, ttl_seconds: int = 120) -> None:
        self._ttl = max(0, ttl_seconds)
        self._entries: dict[str, tuple[float, list[dict[str, Any]], dict[str, Any]]] = {}

    def get(self, branch: str) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
        if self._ttl == 0:
            return None
        entry = self._entries.get(branch)
        if entry is None:
            return None
        timestamp, rows, meta = entry
        if time.monotonic() - timestamp > self._ttl:
            self._entries.pop(branch, None)
            return None
        return rows, meta

    def set(self, branch: str, rows: list[dict[str, Any]], meta: dict[str, Any]) -> None:
        if self._ttl:
            self._entries[branch] = (time.monotonic(), rows, meta)


_STOCK_RUPTURE_CACHE = _StockRuptureSnapshotCache(120)


class DemandService:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        branch_access: BranchAccessService | None = None,
        coverage: DemandCoverageService | None = None,
        myweg_coverage: Any | None = None,
        today: date | None = None,
        cache: _DemandSnapshotCache | None = None,
        stock_rupture_cache: _StockRuptureSnapshotCache | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()
        self._today = today
        self._coverage = coverage or DemandCoverageService(today=today)
        self._myweg_coverage = myweg_coverage
        self._cache = cache if cache is not None else _SNAPSHOT_CACHE
        self._stock_rupture_cache = (
            stock_rupture_cache if stock_rupture_cache is not None else _STOCK_RUPTURE_CACHE
        )

    # ------------------------------------------------------------- helpers

    def _reference_date(self) -> date:
        return self._today or date.today()

    def _authorize(self, user: object | None, *, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_DEMAND_VIEW):
            raise PermissionError("Você não tem permissão para ver a demanda.")

    def _cache_key(self, branch: str, origin: str) -> str:
        if origin == ORIGIN_PROTHEUS:
            return branch
        return f"{branch}|{origin}"

    def _load_protheus_lines(self, branch: str, *, refresh: bool = False) -> list[DemandLine]:
        key = self._cache_key(branch, ORIGIN_PROTHEUS)
        if not refresh:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
        try:
            sales_orders = _unwrap(self._gateway.fetch_open_sales_orders(), "items")
            production_orders = _unwrap(self._gateway.fetch_open_production_orders(), "items")
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError("Não foi possível carregar a demanda em aberto.") from exc

        lines = self._coverage.build(
            open_sales_orders=sales_orders,
            open_production_orders=production_orders,
            branch=branch,
        )
        for line in lines:
            line.source = ORIGIN_PROTHEUS
            line.planning = False
        self._cache.set(key, lines)
        return lines

    def _load_lines(self, branch: str, *, refresh: bool = False) -> list[DemandLine]:
        """Compat: snapshot Protheus da filial (detectores / overview)."""
        return self._load_protheus_lines(branch, refresh=refresh)

    def branch_lines(self, branch: str, *, refresh: bool = False) -> list[DemandLine]:
        """Snapshot da filial sem RBAC — uso interno (detectores / overview)."""
        return self._load_lines(branch, refresh=refresh)

    def _load_origin_lines(
        self,
        user: object | None,
        *,
        branch: str,
        origin: str,
        refresh: bool = False,
    ) -> tuple[list[DemandLine], dict[str, Any] | None]:
        """Carrega linhas conforme origem. Retorna (lines, myweg_meta|None)."""
        if origin == ORIGIN_PROTHEUS:
            return self._load_protheus_lines(branch, refresh=refresh), None

        if branch != DEMAND_SOURCE_BRANCH:
            if origin == ORIGIN_MYWEG:
                raise InvalidBranch(
                    "Necessidades MyWEG na Demanda estão disponíveis apenas na filial 02."
                )
            # both fora da 02 → degrada a Protheus oficial.
            return self._load_protheus_lines(branch, refresh=refresh), {
                "origin": ORIGIN_PROTHEUS,
                "official_aggregate": True,
                "myweg_skipped": "branch_not_02",
                "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
            }

        if not can(user, PC_MYWEG_NEEDS_VIEW):
            if origin == ORIGIN_MYWEG:
                raise PermissionError(
                    "Você não tem permissão para consultar Necessidades WEG."
                )
            return self._load_protheus_lines(branch, refresh=refresh), {
                "origin": ORIGIN_PROTHEUS,
                "official_aggregate": True,
                "myweg_skipped": "missing_myweg_permission",
                "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
            }

        if self._myweg_coverage is None:
            if origin == ORIGIN_BOTH:
                return self._load_protheus_lines(branch, refresh=refresh), {
                    "origin": ORIGIN_PROTHEUS,
                    "official_aggregate": True,
                    "myweg_skipped": "integration_unavailable",
                    "myweg_degraded": True,
                    "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
                }
            raise DelpiGatewayError("Integração MyWEG na Demanda indisponível.")

        cache_key = self._cache_key(branch, origin)
        if not refresh:
            cached_entry = self._cache.get_entry(cache_key)
            if cached_entry is not None:
                return cached_entry

        try:
            resolved = self._myweg_coverage.resolve_demand_origin_lines(
                user, branch=branch, origin=origin
            )
        except Exception as exc:  # noqa: BLE001
            # Em "Ambas", a carteira Protheus permanece acessível se MyWEG falhar.
            if origin == ORIGIN_BOTH:
                return self._load_protheus_lines(branch, refresh=refresh), {
                    "origin": ORIGIN_PROTHEUS,
                    "official_aggregate": True,
                    "myweg_skipped": "myweg_source_failed",
                    "myweg_degraded": True,
                    "myweg_error_type": type(exc).__name__,
                    "adr_status": "ARCHITECTURE_DECISION_REQUIRED",
                }
            if isinstance(exc, DelpiGatewayError):
                raise
            raise DelpiGatewayError(
                "Não foi possível carregar necessidades MyWEG para a Demanda."
            ) from exc

        lines = list(resolved.get("lines") or [])
        meta = dict(resolved.get("meta") or {})
        self._cache.set(cache_key, lines, meta)
        return lines, meta

    # ------------------------------------------------------------ filtering

    def _matches(self, line: DemandLine, query: DemandQuery) -> bool:
        if query.status and line.status != query.status:
            return False
        if query.due_from or query.due_to:
            if line.due_date is None:
                return False
            if query.due_from and line.due_date < query.due_from:
                return False
            if query.due_to and line.due_date > query.due_to:
                return False
        needle = query.search.strip().upper()
        if needle:
            haystack = " ".join(
                (
                    line.customer_name,
                    line.customer_code,
                    line.customer_store,
                    line.sales_order,
                    line.customer_order,
                    line.product_code,
                    line.source,
                )
            ).upper()
            if needle not in haystack:
                return False
        return True

    @staticmethod
    def _customer_key(line: DemandLine) -> str:
        """Identidade estável por código/loja, mesmo entre origens e páginas."""
        code = _text(line.customer_code).upper()
        store = _text(line.customer_store).upper()
        if code:
            return f"code:{code}/{store}"
        return f"name:{_text(line.customer_name).casefold()}"

    def _customer_options(self, lines: Iterable[DemandLine]) -> list[dict[str, str]]:
        """Catálogo da consulta inteira, antes do recorte de clientes e da paginação."""
        options: dict[str, dict[str, str]] = {}
        for line in lines:
            key = self._customer_key(line)
            if key in options:
                continue
            code = _text(line.customer_code)
            store = _text(line.customer_store)
            name = _text(line.customer_name) or code or "Cliente não identificado"
            identifier = f"{code}/{store}" if store else code
            label = f"{name} · {identifier}" if code else name
            options[key] = {"value": key, "label": label}
        return sorted(
            options.values(),
            key=lambda item: (item["label"].casefold(), item["value"]),
        )

    def _sort_key(self, field: str):
        if field == "customer_name":
            return lambda line: (line.customer_name, line.sales_order, line.line_item)
        if field == "product_code":
            return lambda line: (line.product_code, line.due_date or _FAR_FUTURE)
        if field == "open_quantity":
            return lambda line: (line.open_quantity, line.due_date or _FAR_FUTURE)
        if field == "source":
            return lambda line: (line.source, line.due_date or _FAR_FUTURE)
        if field == "status":
            order = {
                STATUS_LATE: 0,
                STATUS_AT_RISK: 1,
                STATUS_COVERED_BY_ORDER: 2,
                STATUS_COVERED_BY_STOCK: 3,
            }
            return lambda line: (order.get(line.status, 9), line.due_date or _FAR_FUTURE)
        return lambda line: (line.due_date or _FAR_FUTURE, line.sales_order, line.line_item)

    # -------------------------------------------------------------- summary

    def _summary(self, lines: Iterable[DemandLine]) -> dict[str, Any]:
        today = self._reference_date()
        rows = list(lines)
        next_due = min(
            (line.due_date for line in rows if line.due_date and line.due_date >= today),
            default=None,
        )
        return {
            "line_count": len(rows),
            "open_quantity": round(sum(line.open_quantity for line in rows), 3),
            "late_line_count": sum(1 for line in rows if line.status == STATUS_LATE),
            "at_risk_line_count": sum(1 for line in rows if line.status == STATUS_AT_RISK),
            "uncovered_quantity": round(sum(line.uncovered_quantity for line in rows), 3),
            "customer_count": len({line.customer_code or line.customer_name for line in rows}),
            "product_count": len({line.product_code for line in rows}),
            "next_due_date": next_due.isoformat() if next_due else None,
        }

    def _horizon(
        self, lines: Iterable[DemandLine], *, split_origin: bool = False
    ) -> list[dict[str, Any]]:
        """Saldo agrupado por semana de entrega; o atraso vira o primeiro balde."""
        today = self._reference_date()
        buckets: dict[str, dict[str, Any]] = {}
        late_key = "late"
        for line in lines:
            if line.due_date is None:
                continue
            if line.due_date < today:
                key, label, start = late_key, "Atrasado", None
            else:
                monday = line.due_date - timedelta(days=line.due_date.weekday())
                key, label, start = monday.isoformat(), monday.isoformat(), monday
            bucket = buckets.setdefault(
                key,
                {
                    "key": key,
                    "label": label,
                    "start_date": start.isoformat() if start else None,
                    "open_quantity": 0.0,
                    "open_quantity_protheus": 0.0,
                    "open_quantity_myweg": 0.0,
                    "line_count": 0,
                    "late": start is None,
                },
            )
            bucket["open_quantity"] += line.open_quantity
            bucket["line_count"] += 1
            if line.source == ORIGIN_MYWEG:
                bucket["open_quantity_myweg"] += line.open_quantity
            else:
                bucket["open_quantity_protheus"] += line.open_quantity

        ordered = sorted(
            buckets.values(),
            key=lambda item: ("" if item["late"] else "1", item["start_date"] or ""),
        )
        limit = setting_int("horizonBuckets", 8)
        trimmed = ordered[: limit + 1] if limit else ordered
        for bucket in trimmed:
            bucket["open_quantity"] = round(bucket["open_quantity"], 3)
            bucket["open_quantity_protheus"] = round(bucket["open_quantity_protheus"], 3)
            bucket["open_quantity_myweg"] = round(bucket["open_quantity_myweg"], 3)
            if not split_origin:
                bucket.pop("open_quantity_protheus", None)
                bucket.pop("open_quantity_myweg", None)
        return trimmed

    # --------------------------------------------------------------- public

    def _load_stock_rupture_rows(
        self, *, branch: str, refresh: bool
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Somente após RBAC; projeção vem do Reports em rota S2S da api-delpi."""
        if not refresh:
            cached = self._stock_rupture_cache.get(branch)
            if cached is not None:
                return cached
        payload = self._gateway.fetch_stock_rupture_pendencies(
            branch=branch, horizon_days=30
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise DelpiGatewayError("Rupturas do Delpi Reports indisponíveis.")
        raw_meta = data.get("meta")
        meta = raw_meta if isinstance(raw_meta, dict) else {}
        if meta.get("branch") and str(meta["branch"]).strip() != branch:
            raise DelpiGatewayError("Rupturas recebidas de filial diferente da solicitada.")
        rows = [row for row in data["items"] if isinstance(row, dict)]
        self._stock_rupture_cache.set(branch, rows, meta)
        return rows, meta

    def list_op_pendencies(
        self,
        user: object | None,
        *,
        branch: str,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Pendências da Gestão à Vista, na mesma alocação da aba Demanda.

        Requer demand.view e RBAC da filial. MyWEG entra somente na filial 02,
        com permissão explícita, no mesmo pool de estoque/OP (origin=both).
        O período do OTD não recorta o horizonte de necessidades abertas.
        """
        code = self._branch_access.assert_valid_branch(branch)
        self._authorize(user, branch=code)
        requested_origin = (
            ORIGIN_BOTH
            if code == DEMAND_SOURCE_BRANCH and can(user, PC_MYWEG_NEEDS_VIEW)
            else ORIGIN_PROTHEUS
        )
        lines, meta = self._load_origin_lines(
            user, branch=code, origin=requested_origin, refresh=refresh
        )
        metadata = meta or {}
        source_status = "complete"
        warning: str | None = None
        if metadata.get("myweg_skipped"):
            source_status = "partial"
            warning = "Necessidades MyWEG indisponíveis; exibindo somente pedidos Protheus."
        elif code == DEMAND_SOURCE_BRANCH and requested_origin == ORIGIN_PROTHEUS:
            source_status = "partial"
            warning = "Sem permissão MyWEG; exibindo somente pedidos Protheus."

        # Falhas de estoque no SB2 tornam a cobertura MyWEG desconhecida.
        # Evitar alertar 'crie OP' nessas condições (falso positivo).
        uncertain_products: set[str] = set()
        if metadata.get("stock_data_complete") is False:
            uncertain_products = {
                line.product_code for line in lines if line.source == ORIGIN_MYWEG
            }
        today = self._today or today_in_timezone("America/Sao_Paulo")
        payload = build_op_pendencies(
            lines, branch=code, today=today, incomplete_products=uncertain_products
        )
        if payload["suppressed_product_count"] > 0:
            source_status = "partial"
            warning = (
                "Alguns produtos foram ocultados porque a cobertura por estoque ou OP "
                "não está confirmada."
            )

        # Falha na fonte Reports não pode apagar a lista de OPs. A origem da
        # ruptura fica visivelmente indisponível, nunca tratada como zero.
        stock_status = "complete"
        stock_as_of: str | None = None
        rupture_items: list[dict[str, Any]] = []
        try:
            stock_rows, stock_meta = self._load_stock_rupture_rows(
                branch=code, refresh=refresh
            )
            rupture_items = build_stock_rupture_pendencies(
                stock_rows, branch=code, today=today, horizon_days=30
            )
            stock_as_of = str(stock_meta.get("asOfDate") or "") or None
        except Exception:  # noqa: BLE001 — falha isolada, sem divulgar detalhes internos
            stock_status = "unavailable"
            source_status = "partial"
            warning = " ".join(filter(None, (
                warning,
                "Rupturas de estoque indisponíveis. As pendências de OP seguem visíveis.",
            )))
        op_items = payload["items"]
        payload.update({
            "items": merge_pendency_items(op_items, rupture_items),
            "count": len(op_items) + len(rupture_items),
            "op_count": len(op_items),
            "stock_rupture_count": len(rupture_items),
            "stock_source_status": stock_status,
            "stock_as_of": stock_as_of,
            "stock_horizon_days": 30,
            "requested_origin": requested_origin,
            "source_status": source_status,
            "warning": warning,
            "refresh_policy": "snapshot_demand_ttl_and_rupture_120s",
        })
        return payload

    def list_demand(
        self,
        user: object | None,
        *,
        branch: str,
        search: str = "",
        status: str = "",
        due_from: str | None = None,
        due_to: str | None = None,
        sort: str | None = None,
        direction: str = "asc",
        page: int = 1,
        page_size: int | None = None,
        refresh: bool = False,
        origin: str | None = None,
        customers: list[str] | None = None,
    ) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        self._authorize(user, branch=code)

        requested_origin = _text(origin).lower() or ORIGIN_PROTHEUS
        if requested_origin not in ALLOWED_ORIGINS:
            requested_origin = ORIGIN_PROTHEUS

        allowed_statuses = setting_list("statuses")
        requested_status = _text(status)
        if requested_status and requested_status not in allowed_statuses:
            requested_status = ""

        allowed_sorts = setting_list("sortFields")
        if "source" not in allowed_sorts:
            allowed_sorts = list(allowed_sorts) + ["source"]
        requested_sort = _text(sort) or setting_str("defaultSort", "due_date")
        if requested_sort not in allowed_sorts:
            requested_sort = setting_str("defaultSort", "due_date")

        max_page_size = setting_int("maxPageSize", 200)
        resolved_size = page_size or setting_int("defaultPageSize", 50)
        resolved_size = max(1, min(int(resolved_size), max_page_size))
        resolved_page = max(int(page or 1), 1)

        query = DemandQuery(
            branch=code,
            search=_text(search),
            status=requested_status,
            due_from=_iso_date(due_from),
            due_to=_iso_date(due_to),
            sort=requested_sort,
            direction="desc" if _text(direction).lower() == "desc" else "asc",
            page=resolved_page,
            page_size=resolved_size,
            origin=requested_origin,
        )

        all_lines, myweg_meta = self._load_origin_lines(
            user, branch=code, origin=requested_origin, refresh=refresh
        )
        effective_origin = (
            _text((myweg_meta or {}).get("origin")).lower()
            if myweg_meta and myweg_meta.get("myweg_skipped")
            else requested_origin
        )
        if effective_origin not in ALLOWED_ORIGINS:
            effective_origin = requested_origin

        matching_lines = [line for line in all_lines if self._matches(line, query)]
        customer_options = self._customer_options(matching_lines)
        selected_customers = list(dict.fromkeys(
            _text(value) for value in (customers or []) if _text(value)
        ))
        selected_set = set(selected_customers)
        filtered = [
            line for line in matching_lines
            if not selected_set or self._customer_key(line) in selected_set
        ]
        filtered.sort(key=self._sort_key(query.sort), reverse=query.direction == "desc")

        total = len(filtered)
        total_pages = (total + query.page_size - 1) // query.page_size if total else 0
        start = (query.page - 1) * query.page_size
        page_items = filtered[start : start + query.page_size]
        today = self._reference_date()

        split_origin = effective_origin in {ORIGIN_MYWEG, ORIGIN_BOTH} and not (
            myweg_meta or {}
        ).get("myweg_skipped")
        official = effective_origin == ORIGIN_PROTHEUS and not split_origin
        summary = self._summary(filtered)
        summary["official_aggregate"] = official
        if split_origin:
            summary["by_origin"] = {
                ORIGIN_PROTHEUS: self._summary(
                    [line for line in filtered if line.source == ORIGIN_PROTHEUS]
                ),
                ORIGIN_MYWEG: self._summary(
                    [line for line in filtered if line.source == ORIGIN_MYWEG]
                ),
            }
            summary["aggregate_policy"] = "ARCHITECTURE_DECISION_REQUIRED"
            summary["unit"] = "MI"
        else:
            summary["by_origin"] = None
            summary["aggregate_policy"] = "protheus_official"

        payload: dict[str, Any] = {
            "branch": code,
            "items": [line.to_dict(today) for line in page_items],
            "summary": summary,
            "horizon": self._horizon(filtered, split_origin=split_origin),
            "filters": {
                "search": query.search,
                "status": query.status,
                "due_from": query.due_from.isoformat() if query.due_from else None,
                "due_to": query.due_to.isoformat() if query.due_to else None,
                "sort": query.sort,
                "direction": query.direction,
                "origin": effective_origin,
                "requested_origin": requested_origin,
                "statuses": list(allowed_statuses),
                "origins": [ORIGIN_PROTHEUS, ORIGIN_MYWEG, ORIGIN_BOTH],
                "customer_options": customer_options,
                "selected_customers": selected_customers,
            },
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total": total,
                "total_pages": total_pages,
                "is_complete": query.page >= total_pages if total_pages else True,
            },
            "myweg": myweg_meta,
        }
        return payload
